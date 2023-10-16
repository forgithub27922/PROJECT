from odoo import models, fields, api


class Sale(models.Model):
    _inherit = 'sale.order.line'

    discount_am = fields.Float('Discount', compute='_cal_discount_amount')

    @api.depends('discount_am', 'price_unit', 'discount')
    def _cal_discount_amount(self):
        for amount in self:
            amount.discount_am = (amount.price_unit * amount.discount)/100


