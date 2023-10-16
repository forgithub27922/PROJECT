# -*- coding: utf-8 -*-


import datetime
import logging

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    # TODO: Find out how to calculate first order date, and what happens after
    # the contract is expired?

    @api.model
    def _get_default_template_id(self):
        result = False
        try:
            result = self.env.ref('grimm_extensions.grimm_contract_default')
        finally:
            return result

    asset_ids = fields.Many2many('grimm.asset.asset', string='Assets')
    sale_order_id = fields.One2many('sale.order', 'subscription_id', string='Sale Order')
    #mro_order_ids = fields.Many2many('grimm.mro.order', string='MRO Order')
    template_id = fields.Many2one(default=_get_default_template_id)
    recurring_order_next_date = fields.Date('Date of Next Order')
    recurring_order_rule_type = fields.Selection(
        [('daily', 'Day(s)'),
         ('weekly', 'Week(s)'),
         ('monthly', 'Month(s)'),
         ('yearly', 'Year(s)'),
         ], 'MRO Order Recurrency', help="MRO Order creation automatically repeat at specified interval", required=True,
        default='monthly')
    recurring_order_interval = fields.Integer(
        'Repeat Every', help="Repeat every (Days/Week/Month/Year)", required=True, default=1)
    object_address = fields.Many2one('grimm.asset.facility', string='Object Address',
                                     track_visibility='onchange')
    partner_contact = fields.Many2one('res.partner', string='Contact', track_visibility='onchange')
    partner_invoice = fields.Many2one('res.partner', string='Invoice', track_visibility='onchange')
    partner_delivery = fields.Many2one(
        'res.partner', string='Delivery', track_visibility='onchange')

    def set_open(self):
        for record in self:
            if not record.date:
                raise UserError(_('Please enter contract end date'))
            if datetime.datetime.strptime(str(record.date), "%Y-%m-%d").date() < datetime.date.today():
                raise UserError(_('Please enter correct end date'))
        return self.write({'state': 'open'})

    def action_sale_order(self):
        sale_order_ids = [contract.sale_order_id.id for contract in self]

        list_view_id = self.env.ref('sale.view_order_tree').id
        form_view_id = self.env.ref('sale.view_order_form').id
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[list_view_id, "tree"], [form_view_id, "form"]],
            "domain": [["id", "in", sale_order_ids]],
            "context": {"create": True},
            "name": "Contracts",
        }
        if len(sale_order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % sale_order_ids
        elif len(sale_order_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = sale_order_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def action_mro_order(self):

        order_ids = []
        for contract in self:
            order_ids.extend(contract.mro_order_ids.ids)

        list_view_id = self.env.ref('mro_base.view_grimm_mro_order_tree').id
        form_view_id = self.env.ref('mro_base.view_grimm_mro_order_form').id
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'grimm.mro.order',
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'domain': ['id', 'in', order_ids],
            'context': {'create': False},
            'name': 'Orders',
        }
        if len(order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % order_ids
        elif len(order_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = order_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    # @api.depends('recurring_invoice_line_ids.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the Contract.
    #     """
    #     for contract in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in contract.recurring_invoice_line_ids:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #         contract.update({
    #             'amount_untaxed': contract.pricelist_id.currency_id.round(amount_untaxed),
    #             'amount_tax': contract.pricelist_id.currency_id.round(amount_tax),
    #             'amount_total': amount_untaxed + amount_tax,
    #         })
    #
    # amount_untaxed = fields.Float(string='Untaxed Amount', readonly=True, compute='_amount_all', track_visibility='always')
    # amount_tax = fields.Float(string='Taxes', readonly=True, compute='_amount_all', track_visibility='always')
    # amount_total = fields.Float(string='Total', readonly=True, compute='_amount_all', track_visibility='always')

    def _calc_next_recurring_order_date(self):
        for contract in self:
            next_date = datetime.datetime.strptime(str(contract.recurring_order_next_date), "%Y-%m-%d")
            contract_end_date = datetime.datetime.strptime(str(contract.date), "%Y-%m-%d")
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            invoicing_period = relativedelta(
                **{periods[contract.recurring_order_rule_type]: contract.recurring_order_interval})
            new_date = next_date + invoicing_period
            if new_date > contract_end_date:
                new_date = datetime.datetime.strptime(str(contract.date), "%Y-%m-%d")
            contract.recurring_order_next_date = new_date.date()

    def create_mro_orders(self):

        if self.state != 'open':
            raise UserError(_('Contract needs to be open in order to generate MRO Orders'))

        if not self.recurring_order_next_date:
            raise UserError(_('Please enter next recurring order date'))

        if not self.date:
            raise UserError(_('Please enter contract end date'))

        for contract in self:
            asset_orders = []
            for asset in contract.asset_ids:
                vals = {
                    'asset_id': asset.id,
                    'asset_facility_id': asset.asset_facility_id.id,
                }
                mro_asset_order = self.env['grimm.mro.asset.order'].create(vals)
                asset_orders.append(mro_asset_order.id)

            vals = {
                'name': '%s/%s' % (contract.name, contract.code,),
                'partner_id': contract.partner_id.id,
                'date_execution': contract.recurring_order_next_date,
                'date_scheduled': contract.recurring_order_next_date,
                'asset_order_ids': [(6, 0, asset_orders)],
                'origin': contract.sale_order_id.id,
            }
            #mro_order = self.env['grimm.mro.order'].create(vals)
            #contract_orders = [mro_order.id]
            #contract_orders.extend(contract.mro_order_ids.ids)
            #contract.update({
            #    'mro_order_ids': contract_orders
            #})
        self._calc_next_recurring_order_date()

    @api.model
    def _cron_generate_mro_orders(self):
        logging.info('Automatic MRO Order generation cron started')
        return True #Odoo13Change
        contracts = self.env['sale.subscription'].search([('state', '=', 'open')])
        count = 0
        today = datetime.date.today()
        for contract in contracts:
            if not contract.recurring_order_next_date:
                continue
            days_before = self.env.ref(
                'grimm_extensions.automatic_mro_order_create_days_in_advance')
            target_date = today + datetime.timedelta(days=int(days_before.value))
            next_order_date = datetime.datetime.strptime(
                str(contract.recurring_order_next_date), "%Y-%m-%d").date()
            if target_date == next_order_date:
                count += 1
                logging.info('Creating MRO Order for contract: %s' % (contract.display_name,))
                contract.create_mro_orders()
        if count > 0:
            logging.info('Total MRO Orders generated: %s' % (count,))
        logging.info('Automatic MRO Order generation cron finished')


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    def _get_taxes(self):
        for line in self:
            fpos_obj = self.env['account.fiscal.position']
            fpos_id = fpos_obj.get_fiscal_position(
                line.analytic_account_id and line.analytic_account_id.partner_id and line.analytic_account_id.partner_id.id)
            fpos = fpos_obj.browse(fpos_id)
            res = line.product_id
            # account_id = res.property_account_income_id and res.property_account_income_id.id
            # if not account_id:
            #     account_id = res.categ_id.property_account_income_categ_id.id
            # account_id = fpos.map_account(account_id)

            taxes = res.taxes_id or False
            tax_id = fpos.map_tax(taxes)
            line.tax_id = tax_id.id

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the Contract line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.analytic_account_id.currency_id, line.quantity,
                                            product=line.product_id, partner=line.analytic_account_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True)
    price_total = fields.Float(compute='_compute_amount', string='Total', readonly=True)
    tax_id = fields.Many2one('account.tax', string='Taxes', compute='_get_taxes', readonly=True)
