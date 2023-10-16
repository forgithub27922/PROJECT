# -*- coding: utf-8 -*-

from odoo import fields, models, api


class OemDetails(models.Model):
    _name = 'sku.fits.to'
    _description = 'This model has information about passend zu'

    sku = fields.Char('SKU', required=True)
    key = fields.Char('Key', required=True)
    value = fields.Char('Value')
    source = fields.Char('Source', required=True)
    product_id = fields.Many2one('product.template', string="Product Template")
