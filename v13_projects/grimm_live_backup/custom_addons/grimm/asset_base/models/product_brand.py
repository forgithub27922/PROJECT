# -*- coding: utf-8 -*-


from odoo import models, fields


class ProductBrand(models.Model):
    _name = 'grimm.product.brand'
    _description = 'Grimm Product Brand'

    name = fields.Char(string='Name')
    product_ids = fields.One2many('product.product', 'product_brand_id', 'Products')
