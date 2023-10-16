# -*- coding: utf-8 -*-

from odoo import models, fields


class PriceCalculationGroup(models.Model):
    _name = 'product.price.group'
    _order = 'name'
    _description = 'Price Calculation Group'

    name = fields.Char(size=40, string="Name", help="Name must be shorter than 40 characters", index=True)
    description = fields.Char(string="Description")

    _sql_constraints = [('name_uniq', 'unique(name)', 'Name must be unique!')]
