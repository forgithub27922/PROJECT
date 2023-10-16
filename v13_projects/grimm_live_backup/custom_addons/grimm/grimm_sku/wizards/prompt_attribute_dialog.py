# -*- coding: utf-8 -*-

from odoo import models, fields


class PromptAttributeDialog(models.TransientModel):
    _name = 'prompt.attribute.dialog'
    _description = 'Prompt Attribute Dialog'

    sku = fields.Char('SKU')
    name = fields.Char('For Attribute')
    attribute_id = fields.Many2one('product.attribute', string="Product Attribute")
    product_id = fields.Many2one('product.template', string="Product Template")
    source = fields.Char('Source')

    def assign_attribute(self):
        SkuMapping = self.env['sku.mapping']
        SkuMapping.create(
            {'partenics_attribute': self.attribute_id.id, 'outsourced_attribute': self.name, 'source': self.source})

        sku_mapping = SkuMapping.with_context(
            {'sku': self.sku, 'prod_id': self.product_id.id, 'source': self.source}).action_sku_mapping()
        if sku_mapping:
            return sku_mapping
