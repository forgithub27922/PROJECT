# -*- coding: utf-8 -*-


from odoo import models, fields


class SalePurchaseLink(models.Model):
    _name = 'grimm.sale.purchase.link'
    _description = 'Grimm sale purchase link'

    product_id = fields.Many2one('product.product', string='Product', readony=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order', readony=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', readony=True)
    serial_number = fields.Char('Serial No')
    picking_id = fields.Many2one('stock.picking', 'Delivery order')
