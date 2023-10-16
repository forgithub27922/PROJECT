from odoo import models


class PricelistItem(models.Model):
    _name = 'product.pricelist.item'
    _inherit = ['product.pricelist.item', 'mail.thread', 'mail.activity.mixin']
