# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = "stock.move"

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        self.ensure_one()
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
        wh_loc_id = self.warehouse_id or self.location_id.get_warehouse() or self.location_dest_id.get_warehouse()
        analytic_loc_id = wh_loc_id and wh_loc_id.account_analytic_id and wh_loc_id.account_analytic_id.id or False
        if res.get('debit_line_vals'):
            res['debit_line_vals']["analytic_account_id"] = analytic_loc_id
        if res.get('credit_line_vals'):
            res['credit_line_vals']["analytic_account_id"] = analytic_loc_id
        if res.get('credit_line_vals'):
            res['credit_line_vals']["analytic_account_id"] = analytic_loc_id
        return res

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    allow_accountmove = fields.Boolean(string="Allow Account Entries")
    internal_pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=False, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    internal_account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False), ('company_id', '=', 'company_id'),('is_off_balance', '=', False)]",
        check_company=True,
        tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=False)


class Picking(models.Model):
    _inherit = "stock.picking"

    def action_cancel(self):
        RuleModels = self.env['stock.rule']
        for picking in self:
            # if (picking.picking_type_code == 'outgoing' and picking.location_dest_id.usage == 'transit') or (picking.picking_type_code == 'incoming' and picking.location_id.usage == 'transit'):
            if picking.picking_type_code == 'incoming' and picking.location_id.usage == 'transit' and picking.state in ['draft', 'waiting', 'confirmed', 'assigned']:
                picking_ids = self.move_ids_without_package.mapped('move_orig_ids').mapped('picking_id')
                p_done = any( picking.state == 'done' for picking in picking_ids )
                if p_done:
                    raise UserError(_("No se puede cancelar, porque la remisión origen ya fue procesada."))
                    return True
                picking_ids.action_cancel()
        self.mapped('move_lines')._action_cancel()
        self.write({'is_locked': True})                    
        return True

# EPL Disponible => EPL/OUT/06333 (OP/05885) ID = 65482 => outgoing => internal => transit
# Apodaca => APO/IN/01322 (OP/05885) ID = 65483 => incoming => transit => internal


    def button_validate(self):
        res = super(Picking, self).button_validate()
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        journal_id = self.company_id.internal_journal_id or False
        date_order = self._context.get('force_period_date', fields.Date.context_today(self))

        RuleModels = self.env['stock.rule']
        for picking in self:
            wh_loc_id = picking.location_id.get_warehouse()
            pricelist_loc_id = wh_loc_id and wh_loc_id.internal_pricelist_id or False
            account_loc_id = wh_loc_id and wh_loc_id.internal_account_id or False
            analytic_loc_id = wh_loc_id and wh_loc_id.account_analytic_id or False
            if wh_loc_id and not wh_loc_id.allow_accountmove:
                continue
            if picking.location_dest_id.usage != 'transit':
                continue
            wh_loc_dest_id = picking.location_dest_id.get_warehouse()
            if not wh_loc_dest_id:
                stock_rule_ids = RuleModels.search([('location_src_id', '=', picking.location_id.id), ('location_id', '=', picking.location_dest_id.id)])
                for stock_rule in stock_rule_ids:
                    for rule in stock_rule.route_id.rule_ids:
                        if rule.id != stock_rule.id:
                            wh_loc_dest_id = rule.warehouse_id
                            _logger.info('------------ ALMACEN %s  %s - %s %s '%(rule.name, rule.propagate_warehouse_id.name, rule.warehouse_id, rule.route_id.name) )
                            break
            pricelist_dest_id = wh_loc_dest_id and wh_loc_dest_id.internal_pricelist_id or False
            account_dest_id = wh_loc_dest_id and wh_loc_dest_id.internal_account_id or False
            analytic_dest_id = wh_loc_dest_id and wh_loc_dest_id.account_analytic_id or False
            _logger.info('------ wh_loc_id %s - %s - %s - %s %s  '%(picking.location_id, wh_loc_id, pricelist_loc_id, account_loc_id, analytic_loc_id ) )
            _logger.info('------ wh_loc_dest_id %s - %s - %s - %s %s  '%(picking.location_dest_id, wh_loc_dest_id, pricelist_dest_id, account_dest_id, analytic_dest_id ) )
            move_lines = []
            debit_lines, credit_lines = [], []
            move_total = 0.0
            todo_moves = self.mapped('move_lines') # .filtered(lambda m: m.state in ['donde'])
            move_state = ''
            for move in todo_moves:
                _logger.info('---- move_state picking.state %s- - %s '%(picking.state, move.state) )
                if move.quantity_done != 0 and move.state == 'done':
                    move_state = move.state
                    product = move.product_id.with_context(
                        partner=False,
                        quantity=move.product_qty,
                        date=date_order,
                        pricelist=account_dest_id and pricelist_dest_id.id or False,
                        uom=move.product_id.uom_id.id
                    )
                    credit_value = product.price * move.product_qty
                    # Debit
                    debit_line_vals = {
                        'name': move.product_id.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_qty,
                        'product_uom_id': move.product_id.uom_id.id,
                        'ref': move.product_id.name,
                        'partner_id': False,
                        'credit': 0,
                        'debit': credit_value,
                        'account_id': account_dest_id and account_dest_id.id or False,
                        'analytic_account_id': analytic_dest_id and analytic_dest_id.id or False,
                        'price_unit': product.price or 0.0
                    }
                    debit_lines.append((0, 0, debit_line_vals))
                    # credit
                    credit_line_vals = {
                        'name': move.product_id.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_qty,
                        'product_uom_id': move.product_id.uom_id.id,
                        'ref': move.product_id.name,
                        'partner_id': False,
                        'credit': credit_value,
                        'debit': 0,
                        'account_id': account_loc_id and account_loc_id.id or False,
                        'analytic_account_id': analytic_loc_id and analytic_loc_id.id or False,
                        'price_unit': product.price or 0.0
                    }
                    credit_lines.append((0, 0, credit_line_vals))
                    move_total += credit_value
            if picking.state == 'done' and move_total != 0.0:
                move_lines = credit_lines + debit_lines
                AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id.id)
                move_vals = {
                    'journal_id': journal_id.id,
                    'line_ids': move_lines,
                    'date': date_order,
                    'ref': 'Transferencias Internas %s '%( picking.name ),
                    'move_type': 'entry',
                }
                new_account_move = AccountMove.sudo().create(move_vals)
                new_account_move._post()
                new_account_move.write({
                    'ref': 'Transferencias Internas %s '%( picking.name )
                })
                _logger.info('-------- stocktransfer-accountmove %s '%(new_account_move) )
        return res
