# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductUpdateQueue(models.Model):
    _name = 'product.update.queue'
    _description = 'Product update queue'
    _order = 'write_date desc, id'

    product_id = fields.Many2one(comodel_name='product.product', required=True, index=True, ondelete='cascade')

    _sql_constraints = [
        ('Product_Unique', 'unique(product_id)', 'Product must be unique!'),
    ]
