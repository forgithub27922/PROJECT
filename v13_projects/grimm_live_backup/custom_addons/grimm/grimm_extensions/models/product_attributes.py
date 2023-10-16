# -*- coding: utf-8 -*-


from odoo import models, fields


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    print_attrib = fields.Boolean(string='Print on Report', default=False)
    print_seq = fields.Integer(string='Sequence for Report Printing', default=10,
                               help="The sequence of this line when displayed in report")


class ProductAttributesData(models.Model):
    _inherit = 'product.attributes.data'

    print_attrib = fields.Boolean('Print on Report', related='attr_id.print_attrib')
    print_seq = fields.Integer('Sequence for Report Printing', related='attr_id.print_seq',
                               help="The sequence of this line when displayed in report")
