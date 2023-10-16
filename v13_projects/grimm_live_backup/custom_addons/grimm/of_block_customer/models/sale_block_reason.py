# -*- coding: utf-8 -*-


from odoo import fields, models


class SaleBlockReason(models.Model):
    _name = 'sale.block.reason'
    _description = 'Sale Block Reason'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
