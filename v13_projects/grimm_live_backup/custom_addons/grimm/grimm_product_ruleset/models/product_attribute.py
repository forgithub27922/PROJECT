# -*- coding: utf-8 -*-


from odoo import fields, models, api


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    attr_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('entity', 'Entity'),
        ('filler', 'Filler')
    ], string='Shopware Type', required=True, default='char')

    uom = fields.Many2one('uom.uom', string='Unit')
    entity_id = fields.Many2one('ir.model.fields', string='Entity')
    content = fields.Char('Content')

    @api.onchange('attr_type')
    def _get_product_fields(self):
        for rec in self:
            if rec.attr_type == 'entity':
                prod_fields = self.env['ir.model.fields'].search(
                    [('model_id', '=', self.env['ir.model'].search([('model', '=', 'product.product')]).id)])
                return {'domain': {'entity_id': [('id', 'in', [field.id for field in prod_fields if field.ttype not in
                                                               ['one2many', 'many2many', 'selection', 'binary']])]}}
