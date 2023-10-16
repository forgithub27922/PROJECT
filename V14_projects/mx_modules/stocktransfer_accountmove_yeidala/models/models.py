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


class Company(models.Model):
    _inherit = "res.company"

    internal_journal_id = fields.Many2one(
        'account.journal', 'Internal Journal', ondelete="restrict", check_company=True,
        help="Technical field used for resupply routes between warehouses that belong to this company")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_journal_id = fields.Many2one(related='company_id.internal_journal_id', readonly=False)


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
                print('00001')
                continue
            if picking.location_dest_id.usage != 'transit':
                print('00002')
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
                    print('---- debit_line_vals', debit_line_vals)
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
