# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        result = super(PurchaseOrder, self).button_confirm()
        for record in self:
            for picking in record.picking_ids:
                sale_purchase_ids = self.env['grimm.sale.purchase.link'].search(
                    [('purchase_id', '=', record.id)])
                sale_purchase_ids.write({'picking_id': picking.id})
                picking.sale_purchase_link = sale_purchase_ids
        return result

    def open_sale_order_view(self):
        sale_ids = []
        if self.origin:
            for origin in self.origin.split(','):
                sale = self.env["sale.order"].search([('name', '=', origin.strip())], limit=1)
                sale_ids.append(sale.id)
        return {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'views': [(False, 'tree'),(False, 'form')],
            'target': 'current',
            'domain': [('id', 'in', sale_ids)],
        }

    po_date = fields.Datetime(string="Order Date")
    sale_count = fields.Integer(compute="_compute_sales",
                                string='Sales count', copy=False, default=0)
    oc_received_date = fields.Datetime(string="Order Confirmation received Date")
    sale_order_client_order_refs = fields.Char(compute="_compute_customer_refs", string='Kundenreferenz', copy=False)

    @api.depends('origin')
    def _compute_customer_refs(self):
        for order in self:
            sale_pool = self.env['sale.order']
            client_ref = ""
            count = 0
            if order.origin:
                for origin in order.origin.split(','):
                    sales = sale_pool.search([('name', '=', origin)])
                    for sale in sales:
                        if count > 0 and sale.client_order_ref:
                            client_ref += ","
                        if sale.client_order_ref:
                            client_ref = ' '.join((client_ref, sale.client_order_ref)).encode('utf-8')
                        count += 1
            order.sale_order_client_order_refs = client_ref

    @api.depends('origin')
    def _compute_sales(self):
        for order in self:
            sale_pool = self.env['sale.order']
            counter = 0
            if order.origin:
                for origin in order.origin.split(','):
                    sales = sale_pool.search([('name', '=', origin.strip())])
                    counter += len(sales)
            order.sale_count = counter

    @api.model
    def create(self, vals):
        result = super(PurchaseOrder, self).create(vals)
        result.po_date = fields.Datetime.now()
        # Added code for populate pre text when we create PO from SO. Ticket #OD-709
        if result.salutation_text_tmpl_id:
            result.salutation_text = result.salutation_text_tmpl_id.render_template(result.salutation_text_tmpl_id.text, result)
        if result.salutation_text_po_tmpl_id:
            result.salutation_text_po = result.salutation_text_po_tmpl_id.render_template(result.salutation_text_po_tmpl_id.text, result)
        for line in result.order_line:
            if len(line.taxes_id) > 1 and self.env.user.id > 2:
                raise ValidationError(_(
                    'You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(
                        line.product_id.display_name)))
        return result

    def write(self, vals):
        result = super(PurchaseOrder, self).write(vals)
        for res in self:
            for line in res.order_line:
                if len(line.taxes_id) > 1 and self.env.user.id > 2:
                    raise ValidationError(_(
                        'You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(
                            line.product_id.display_name)))
        return result

    def order_confirmed(self):
        self.oc_received_date = fields.datetime.now()
        try:
            self.write({'po_review_state': 'finish'})
        except:
            pass

