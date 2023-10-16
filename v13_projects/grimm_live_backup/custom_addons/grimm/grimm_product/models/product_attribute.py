# -*- coding: utf-8 -*-


from odoo import fields, models, api


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    variant_attribute = fields.Boolean(string='Use to create variant products?', default=True)
    use_in_products = fields.Boolean(string='Use in products?', compute='_compute_use_in_products', store=True)

    @api.depends('write_date')
    def _compute_use_in_products(self):
        for record in self:
            record.use_in_products = True

    @api.model
    def _get_name_search_domain(self):
        ctx = self.env.context

        res_domain = []
        manual_domain = False

        if 'search_from_attr_set' in ctx:
            manual_domain = True

            if not ctx['search_from_attr_set']:
                return manual_domain, []

            attribute_set_id = int(ctx['search_from_attr_set'])
            attribute_set = self.env['product.attribute.set'].browse(attribute_set_id)
            res_domain.append(('id', 'in', [x.id for x in attribute_set.product_attribute_ids.filtered(
                lambda rec: rec.use_in_products is True)]))

        if ctx.get('variant_only', False):
            manual_domain = True
            res_domain.append(('variant_attribute', '=', True))

        return manual_domain, res_domain

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        is_manual, manual_domain = self._get_name_search_domain()

        if is_manual and not manual_domain:
            return []

        if manual_domain:
            args = manual_domain

        return super(ProductAttribute, self).name_search(name, args, operator, limit)


class ProductAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    @api.onchange('attribute_id')
    def onchange_attribute_id(self):
        self.value_ids = self.attribute_id.value_ids
