# -*- coding: utf-8 -*-

from odoo import models, fields


class PromptSkuExists(models.TransientModel):
    _name = 'prompt.sku.exists.dialog'
    _description = 'Prompt Sku Exists'

    name = fields.Char('Vendor Product Code')
    source = fields.Char('Source')

    def scrape_sparepart_add_again_action(self):
        active_ids, sku_vendor_codes, prod_id, brand = self.env.context.get('active_ids'), self.env.context.get(
            'sku_vendor_codes'), self.env.context.get('active_id'), self.env.context.get('brand')
        print('you want to scrap again', active_ids, sku_vendor_codes, prod_id, brand)
        ScrapeSparepartDialog = self.env['scrape.sparepart.dialog']
        if self.source == 'GP':
            spare_parts = ScrapeSparepartDialog.fetch_data_gastroparts(self.name, prod_id, brand)
        elif self.source == 'MO':
            spare_parts = ScrapeSparepartDialog.fetch_data_mercateo(self.name, prod_id, brand)

        res = ScrapeSparepartDialog.insert_or_update_sparepart(spare_parts, prod_id)

        if res:
            sku_mapping = self.env['sku.mapping'].with_context(
                {'sku': self.name, 'prod_id': prod_id, 'active_ids': active_ids,
                 'source': self.source}).action_sku_mapping()
            if sku_mapping:
                return sku_mapping

        sku_attr_prod = ScrapeSparepartDialog.assign_attributes2product(self.name,
                                                                        self.env['product.template'].browse(prod_id),
                                                                        self.source)
        if sku_attr_prod:
            return sku_attr_prod

        if active_ids and sku_vendor_codes:
            act_prod_action = self.execute_active_products(active_ids, sku_vendor_codes, self.source)
            if act_prod_action:
                return act_prod_action

    def scrape_sparepart_skip_action(self):
        active_ids, sku_vendor_codes, prod_id = self.env.context.get('active_ids'), self.env.context.get(
            'sku_vendor_codes'), self.env.context.get('active_id')
        print('Vielen dank für skipping', active_ids, sku_vendor_codes)
        sku_mapping = self.env['sku.mapping'].with_context(
            {'sku': self.name, 'prod_id': prod_id, 'active_ids': active_ids,
             'source': self.source}).action_sku_mapping()
        if sku_mapping:
            return sku_mapping

        sku_attr_prod = self.env['scrape.sparepart.dialog'].assign_attributes2product(self.name, self.env[
            'product.template'].browse(prod_id), self.source)
        if sku_attr_prod:
            return sku_attr_prod

        if active_ids and sku_vendor_codes:
            act_prod_action = self.execute_active_products(active_ids, sku_vendor_codes, self.source)
            if act_prod_action:
                return act_prod_action

    def execute_active_products(self, active_ids, sku_vendor_codes, source):
        ctx = {'source': self.source, 'active_ids': active_ids, 'sku_vendor_codes': sku_vendor_codes, 'source': source}
        action_spare_part = self.env['scrape.sparepart.dialog'].with_context(ctx).scrape_sparepart_action()
        if action_spare_part:
            return action_spare_part
