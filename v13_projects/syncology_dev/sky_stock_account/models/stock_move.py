from odoo import fields, models,api


class StockMove(models.Model):
    _inherit = 'stock.move'

    price = fields.Float('Price', compute='_compute_price', store= True)
    subtotal = fields.Float(string='SubTotal', compute='_compute_subtotal')

    @api.depends('product_id')
    def _compute_price(self):
        for rec in self:
            if rec.product_id:
                rec.price = rec.product_id.lst_price

    @api.depends('price','product_uom_qty')
    def _compute_subtotal(self):
        for move in self:
            move.subtotal = move.price * move.product_uom_qty














