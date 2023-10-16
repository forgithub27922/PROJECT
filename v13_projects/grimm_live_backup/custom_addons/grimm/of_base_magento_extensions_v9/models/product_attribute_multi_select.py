# -*- coding: utf-8 -*-


from odoo import models, fields


class ProductAttributesData(models.Model):
    _inherit = 'product.attributes.data'
    _description = 'Product attributes data'

    is_required = fields.Boolean(related='attr_id.is_required')


class ProductMultiSelectAttributesData(models.Model):
    _name = 'product.attributes.data.multi_select'
    _description = 'Product attributes data multi select'
    _inherit = 'product.attributes.data'

    is_required = fields.Boolean(related='attr_id.is_required')
    value_ids = fields.Many2many(comodel_name='product.template.attribute.value', column1='attribute_data_id',
                                 column2='attribute_value_id', relation='product_attribute_value_multi_select_rel',
                                 copy=True, string='Values')
