# -*- coding: utf-8 -*-


from odoo import fields, models, api

class ProductTemplateShopware(models.Model):
    _inherit = "shopware.property.line"

    uom = fields.Many2one(related='attribute_id.uom', string='Unit')
    entity_id = fields.Many2one(related='attribute_id.entity_id', string='Entity')
    attr_type = fields.Selection(string='Shopware Type', related='attribute_id.attr_type')


class PropertySet(models.Model):
    _inherit = 'property.set'

    @api.model
    def create(self, vals):
        res = super(PropertySet, self).create(vals)
        for attr in vals.get('product_attribute_ids', False)[0][2]:
            vals_line = {
                'property_id': res.id,
                'attribute_id': attr,
                'ruleset_id': False,
            }
            self.env['ruleset.attribute.line'].sudo().create(vals_line)
        return res

    def write(self, vals):
        if 'product_attribute_ids' in vals:
            attr_lst = [attr for attr in vals['product_attribute_ids'][0][2]]
            res = self.env['ruleset.attribute.line'].sudo().search([('property_id', '=', self.id), ('ruleset_id', '=', False)])
            for attr in res:
                if attr.attribute_id.id not in attr_lst:
                    attr.unlink()

            for attr in attr_lst:
                if attr not in [attribute.id for attribute in res]:
                    vals_line = {
                        'property_id': self.id,
                        'attribute_id': attr,
                        'ruleset_id': False,
                    }
                    self.env['ruleset.attribute.line'].sudo().create(vals_line)

        return super(PropertySet, self).write(vals)
