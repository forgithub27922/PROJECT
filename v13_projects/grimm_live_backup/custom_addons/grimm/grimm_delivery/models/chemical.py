# -*- coding: utf-8 -*-

from odoo import models, fields

class UNNumber(models.Model):
    _name = 'un.number'
    _description = 'UN Number'

    name = fields.Char(string='UN Number', required=True, help='UN Number')
    description = fields.Char(string='Description', required=True, help='Description for delivery note')


class TransportCategory(models.Model):
    _name = 'transport.category'
    _description = 'Transport Category'
    _order = 'name, id'

    name = fields.Char(string='Transport Category', required=True, help='Transport Category')
    factor = fields.Integer(string='Multiplication Factor', help='Multiplication Factor')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    un_number = fields.Many2one(comodel_name="un.number", string='Un Number', related='product_variant_ids.un_number', readonly=False)
    trans_categ_id = fields.Many2one(comodel_name="transport.category", string='Transport Category', related='product_variant_ids.trans_categ_id', readonly=False)
class ProductProduct(models.Model):
    _inherit = 'product.product'

    un_number = fields.Many2one(comodel_name="un.number", string='Un Number')
    trans_categ_id = fields.Many2one(comodel_name="transport.category", string='Transport Category')

