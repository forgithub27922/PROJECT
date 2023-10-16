# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    magento_tax_class_id = fields.Many2one(string='Magento Tax Class', comodel_name='product.attribute.value',
                                           domain=[('attribute_id.technical_name', '=', 'tax_class_id')],
                                           default=False
                                           )
