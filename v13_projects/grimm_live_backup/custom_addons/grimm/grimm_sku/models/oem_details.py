# -*- coding: utf-8 -*-

from odoo import fields, models, api


class OemDetails(models.Model):
    _name = 'sku.oem.details'
    _description = 'This model contains oem_details'

    sku = fields.Char('SKU', required=True)
    brand = fields.Char('Brand', required=True)  # 'brand' is taken for mapping
    brand_sku = fields.Char('Brand SKU')
    source = fields.Char('Source', required=True)
    product_id = fields.Many2one('product.template', string="Product Template")
