# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OemDetails(models.Model):
    _name = 'sku.technical.details'
    _description = 'All scraped technical information is stored'

    sku = fields.Char('SKU', required=True)
    key = fields.Char('Key', required=True)
    value = fields.Char('Value', required=True)
    source = fields.Char('Source', required=True)
    product_id = fields.Many2one('product.template', string="Product Template")
