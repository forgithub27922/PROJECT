# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pricelist_status = fields.Datetime('Pricelist Status')
    next_price_update = fields.Date('Nächstes Preisupdate', help="Nächstes Preisupdate",
                                    track_visibility='onchange')
    features = fields.Char('Special Features')
    telephone_advice_fee = fields.Char('Telephone Advice Fee')
    island_surcharges = fields.Char('Island Surcharges')
    others = fields.Char('Others')
    freight_paid_de_mainland = fields.Char('Carriage Paid from (German Mainland)')
    delivery_eu = fields.Boolean('Delivery EU')
    delivery_switzerland = fields.Boolean('Delivery Switzerland')
    delivery_3rd_countries = fields.Boolean('Delivery third countries')
    merchandise = fields.Char('Merchandise')
    accessories = fields.Char('Accessories')
    spare_part = fields.Char('Spare Part')
    product_info = fields.Boolean('Product Info')
    technical_sketch = fields.Boolean('Technical Sketch')
    photos = fields.Boolean('Photos')
    texts = fields.Boolean('Texts')
    min_qty_surcharge = fields.Char('minimum quantity surcharge')
    transport_cost_insurance = fields.Char('Transport costs insurance')
    product_brand_id = fields.Many2many('grimm.product.brand', string='Brand')
    fees_particular = fields.Text('Fees Particulars')
    delivery_particular = fields.Text('Delivery Particulars')
    agreement_particular = fields.Text('Agreement Particulars')
    return_particular = fields.Text('Return Particulars')
    supplier_folder = fields.Char('Supplier Folder')
    customer = fields.Boolean(string="Ist ein Kunde", default=False)
    supplier = fields.Boolean(string="Ist ein Lieferant", default=False)

    @api.onchange('customer')
    def onchange_customer(self):
        if self.customer:
            if self.customer_rank < 1:
                self.customer_rank = 1
        else:
            self.customer_rank = 0

    @api.onchange('supplier')
    def onchange_supplier(self):
        if self.supplier:
            if self.supplier_rank < 1:
                self.supplier_rank = 1
        else:
            self.supplier_rank = 0

    @api.model
    def _default_payment_term(self):
        payment_term = self.env['accoung.payment.term'].search(
            [('name', '=', '14 days net')])
        if not payment_term:
            return False
        if len(payment_term) > 1:
            payment_term = payment_term[0]
        return payment_term.id

    @api.model
    def _default_carrier_id(self):
        carrier = self.env['delivery.carrier'].search(
            [('name', '=', 'Standardversand innerhalb Deutschland')])
        if not carrier:
            return False
        if len(carrier) > 1:
            carrier = carrier[0]
        return carrier.id

    parent_partner_print = fields.Boolean(string='External Address', default=False)
    sold_products = fields.Integer(string="Sold Products", compute="_get_sold_products")
    own_customer_ref = fields.Char(string='Own Customer Reference')

    def _get_sold_products(self):
        for record in self:
            sum_quantity = 0
            if record.id != record.company_id.partner_id.id:
                paid_invoice = self.env['account.move'].search(
                    [('partner_id', '=', record.id), ('state', 'in', ('open', 'paid'))])
                sold_products = self.env['account.move.line'].search(
                    [('move_id', 'in', paid_invoice.ids)])
                for products in sold_products:
                    # if products.product_id.product_tmpl_id.type == 'product':
                    sum_quantity = sum_quantity + products.quantity
                record.sold_products = sum_quantity

    def get_related_products(self):
        ctx = self._context.copy()

        paid_invoice = self.env['account.move'].sudo().search(
            [('partner_id', 'in', self.ids), ('state', 'in', ('open', 'paid'))])
        sold_products = self.env['account.move.line'].search(
            [('move_id', 'in', paid_invoice.ids)])

        form_view_id = self.env.ref('account.view_invoice_line_form')
        tree_view_id = self.env.ref('account.view_invoice_line_tree')
        result = {
            'name': _('Sold Products'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'views': [(tree_view_id.id or False, 'tree'),
                      (form_view_id.id or False, 'form')],
            'target': 'current',
            'context': ctx,
            'domain': [('id', 'in', sold_products.ids)],
        }
        return result
