# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SkuMapping(models.Model):
    _name = 'sku.mapping'
    _description = 'Mapped attribute with outsourced attribute for SKU is stored'

    partenics_attribute = fields.Many2one('product.attribute', string='Partenics Attribute', required=True)
    outsourced_attribute = fields.Char('Outsourced Attribute', required=True)
    source = fields.Char('Source', required=True)

    def action_sku_mapping(self):
        print('Printing context ....', self.env.context)
        tech_dtls = self.env['sku.technical.details'].search(
            [('sku', '=', self.env.context.get('sku')), ('source', '=', self.env.context.get('source')),
             ('product_id', '=', self.env.context.get('prod_id'))])
        print('CHECK TECH DTLS', tech_dtls)

        for rec in tech_dtls:
            hasAttr = self.search([('outsourced_attribute', '=', rec.key), ('source', '=', rec.source)])
            if not hasAttr:
                partenics_attr = self.env['product.attribute'].search(
                    [('name', '=', rec.key), ('technical_name', '=ilike', 'sw_%')], limit=1)
                if partenics_attr:
                    self.create({'partenics_attribute': partenics_attr.id, 'outsourced_attribute': rec.key,
                                 'source': rec.source})
                    continue
                else:
                    return {
                        "type": "ir.actions.act_window",
                        "res_model": "prompt.attribute.dialog",
                        "views": [[self.env.ref('grimm_sku.prompt_attribute_dialog_form').id, "form"]],
                        'context': {'default_name': rec.key, 'default_source': rec.source, 'default_sku': rec.sku,
                                    'default_product_id': self.env.context.get('prod_id', False)},
                        "target": "new"
                    }
        if 'prod_id' in self.env.context and self.env.context.get('prod_id'):
            attr = self.env['scrape.sparepart.dialog'].assign_attributes2product(self.env.context.get('sku'),
                                                                                 self.env['product.template'].browse(
                                                                                     self.env.context.get('prod_id')),
                                                                                 self.env.context.get('source'))
            if attr:
                return attr

    def action_scrape_sparepart(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "scrape.sparepart.dialog",
            "views": [[self.env.ref('grimm_sku.scrape_sparepart_dialog_form').id, "form"]],
            "context": {'active_model': 'sku.mapping', 'active_ids': False},
            "target": "new"
        }
