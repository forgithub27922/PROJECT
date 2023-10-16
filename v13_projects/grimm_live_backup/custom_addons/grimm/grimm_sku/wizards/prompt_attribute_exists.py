# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PromptAttributeExists(models.TransientModel):
    _name = 'prompt.attribute.exists.dialog'
    _description = 'Prompt Attribute Exists Dialog'

    sku = fields.Char('SKU')
    source_product = fields.Char('Source Product')
    product_id = fields.Many2one('product.template', string='GRIMM Product')
    attribute_id = fields.Many2one('product.attribute', string='Attribute')
    mapping_m2m_char = fields.Char('Mapping')
    source = fields.Char('Source')

    def add_attribute_action(self):
        print('Add action!', self.product_id, self.attribute_id)
        attr_ids = self.product_id.property_set_id.product_attribute_ids
        lst_attrs = [pattr for pattr in attr_ids.ids]
        lst_attrs.append(self.attribute_id.id)
        SkuMapping = self.env['sku.mapping']
        if self.product_id.property_set_id:
            self.product_id.property_set_id.product_attribute_ids = [(6, 0, lst_attrs)]
        else:
            raise ValidationError(_('Please assign a property set for the product %s' % self.product_id.name))

        get_outsource_attributes = self.env['sku.technical.details'].search(
            [('sku', '=', self.sku), ('source', '=', self.source), ('product_id', '=', self.product_id.id)])
        if not get_outsource_attributes:
            get_outsource_attributes = self.env['sku.technical.details'].search(
                [('sku', '=', self.sku), ('source', '=', self.source)])
        sku_recs = SkuMapping.search(
            [('outsourced_attribute', 'in', [os_attr.key for os_attr in get_outsource_attributes]),
             ('partenics_attribute', '=', self.attribute_id.id), ('source', '=', self.source)])
        sku_rec = [rec for rec in sku_recs if rec.partenics_attribute.id == self.attribute_id.id][0]

        _logger.info('CHECK FOR THE RIGHT SKU MAPPING RECORD' + str(sku_rec.outsourced_attribute))

        if self.attribute_id.id not in [attr.attribute_id.id for attr in self.product_id.shopware_property_ids]:
            val = self.env['sku.technical.details'].search(
                [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', self.sku), ('source', '=', self.source), ('product_id', '=', self.product_id.id)]).value
            if not val:
                val = self.env['sku.technical.details'].search(
                    [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', self.sku), ('source', '=', self.source)]).value

            if val and val not in [val.name for val in sku_rec.partenics_attribute.value_ids]:
                sku_rec.partenics_attribute.value_ids = [(0, 0, dict(name=val))]

            val_rec = [aval.id for aval in sku_rec.partenics_attribute.value_ids if aval.name == val]
            self.product_id.shopware_property_ids = [
                (0, 0, dict(attribute_id=self.attribute_id.id, value_ids=[(6, 0, val_rec)]))]
        else:
            val = self.env['sku.technical.details'].search(
                [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', self.sku), ('source', '=', self.source), ('product_id', '=', self.product_id.id)]).value
            if not val:
                val = self.env['sku.technical.details'].search(
                    [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', self.sku), ('source', '=', self.source)]).value

            _logger.info('VAlue from Attribute [ELSE]================' + str(val))
            if val and val not in [val.name for val in sku_rec.partenics_attribute.value_ids]:
                sku_rec.partenics_attribute.value_ids = [(0, 0, dict(name=val))]

            val_rec = [aval.id for aval in sku_rec.partenics_attribute.value_ids if aval.name == val]
            rec_shop = [attr for attr in self.product_id.shopware_property_ids if
                        attr.attribute_id.id == self.attribute_id.id]
            self.product_id.shopware_property_ids = [
                (1, rec_shop[0].id, dict(value_ids=[(6, 0, val_rec)]))]

        sku_recs = SkuMapping.browse(
            [int(s) for s in self.mapping_m2m_char.split(',')] if self.mapping_m2m_char else False)
        dia_attr = self.env['scrape.sparepart.dialog'].dialog_attributes2product(self.sku,
                                                                                 self.product_id, sku_recs,
                                                                                 self.mapping_m2m_char.split(
                                                                                     ',') if self.mapping_m2m_char else [],
                                                                                 self.source)

        if dia_attr:
            return dia_attr

    def skip_attribute_action(self):
        print('Skip action!', self.product_id, self.attribute_id)
        sku_recs = self.env['sku.mapping'].browse(
            [int(s) for s in self.mapping_m2m_char.split(',')] if self.mapping_m2m_char else False)
        dia_attr = self.env['scrape.sparepart.dialog'].dialog_attributes2product(self.sku, self.product_id, sku_recs,
                                                                                 self.mapping_m2m_char.split(
                                                                                     ',') if self.mapping_m2m_char else [],
                                                                                 self.source)
        if dia_attr:
            return dia_attr

    def skip_product_action(self):
        active_ids = self.env.context.get('active_ids')
        print('SKIP SKEEP ', active_ids)
        products = self.env['product.template'].browse(active_ids)
        sku_vendor_codes = ''
        lst_vendor_codes = []
        for prod in products:
            sku = [sku_rec.product_code for sku_rec in prod.sudo().seller_ids if
                   sku_rec.product_code and sku_rec.name.id not in [1, 83602, 7393, 9567, 33147, 14655, 24357, 24404]]
            if sku:
                lst_vendor_codes.append(sku[0])

        if lst_vendor_codes:
            sku_vendor_codes = ', '.join(lst_vendor_codes)

        ctx = {'source': self.source, 'active_ids': active_ids, 'sku_vendor_codes': sku_vendor_codes,
               'source': self.source}
        action_scrape = self.env['scrape.sparepart.dialog'].with_context(ctx).scrape_sparepart_action()

        if action_scrape:
            return action_scrape
