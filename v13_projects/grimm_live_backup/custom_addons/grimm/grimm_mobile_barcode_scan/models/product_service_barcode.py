# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductServiceBarcode(models.Model):
    _name = 'product.service.barcode'
    _description = 'Product service barcode'

    product_barcode = fields.Char('Product Barcode')
    prod_default_code = fields.Char('Product Default Code')
    task = fields.Char('Task')
    product = fields.Char('Product')
    qty = fields.Integer('Quantity')
    task_id = fields.Many2one('project.task', string='Task ID')
    user_id = fields.Many2one('res.users', string='User')
    transferred = fields.Boolean('Transferred')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    prod_serv_barcode = fields.One2many('product.service.barcode', 'task_id', string='Product Service Barcode')
    service_travel = fields.One2many('service.travel', 'task_id', string='Service Travel')

    def action_transfer(self):
        for rec in self.prod_serv_barcode.sorted(key=lambda r: r.product_barcode):
            rec.transferred = True
            product = self.env['product.product'].sudo().search(
                ['|', ('barcode', '=', rec.product_barcode), ('default_code', '=', rec.product_barcode)], limit=1)
            # print('UOM', self.env.ref('product.product_uom_unit'), product, self.sale_line_id.order_id)
            # product.uom_id = self<<<<<<f.env.ref('product.product_uom_unit')

            so_line = self.env['sale.order.line'].search(
                [('order_id', '=', self.sale_order_id.id), ('task_id', '=', self.id),
                 ('product_id', '=', product.id)])
            # print(so_line)
            if not so_line:
                vals_so = {
                    'product_id': product.id,
                    'internal_cat': product.categ_id.name,
                    'product_uom':  product.uom_id.id,
                    'product_uom_qty': float(rec.qty),
                    'qty_delivered': 0.0,
                    'qty_invoiced': 0.0,
                    'price_unit': product.calculated_magento_price,
                    'tax_id': [(6, 0, [product.taxes_id.id])],
                    'discount': 0.0,
                    'price_subtotal': product.calculated_magento_price,
                    'name': '',
                    'route_id': False,
                    'order_id': self.sale_order_id.id,
                    'task_id': self.id,
                    'customer_lead': self.env['sale.order']._get_customer_lead(product.product_tmpl_id),
                }
                # lst_scans.append(rec.product_barcode)
                self.env['sale.order.line'].sudo().create(vals_so)
            else:
                lst_qty = [fltrd_rec.qty for fltrd_rec in self.prod_serv_barcode.filtered(lambda r: r.product_barcode == rec.product_barcode)]
                so_line.write({'product_uom_qty': sum(lst_qty)})
                # print(so_line)

        return True


class Timesheets(models.Model):
    _inherit = 'account.analytic.line'

    travel_cost = fields.Selection([('anfahrtspauschale berlin (ap i)', 'Anfahrtspauschale Berlin (AP I)'), ('anfahrtspauschale ii (ap 2)', 'Anfahrtspauschale II (AP 2)'), ('keine anfahrt', 'Keine Anfahrt')], string='Anfahrtspauschale', default='anfahrtspauschale berlin (ap i)')
