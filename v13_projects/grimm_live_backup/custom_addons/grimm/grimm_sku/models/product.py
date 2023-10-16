# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _name = 'sku.product.name'
    _description = 'Scraped product names are stored'

    sku = fields.Char('SKU', required=True)
    name = fields.Char('Name', required=True)
    source = fields.Char('Source', required=True)
    product_id = fields.Many2one('product.template', string="Product Template")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_scrape_sparepart(self, active_ids=False):
        products = self.browse(active_ids)
        sku_vendor_codes, prod_brands = '', ''
        lst_vendor_codes, lst_prod_brands = [], []
        for prod in products:
            sku = [sku_rec.product_code for sku_rec in prod.sudo().seller_ids if
                   sku_rec.product_code and sku_rec.name.id not in [1, 83602, 7393, 9567, 33147, 14655, 24357, 24404]]
            if sku:
                lst_vendor_codes.append(sku[0])

            if prod.product_brand_id:
                lst_prod_brands.append(prod.product_brand_id.name)

        if lst_vendor_codes:
            sku_vendor_codes = ', '.join(lst_vendor_codes)

        if lst_prod_brands:
            prod_brands = ', '.join(lst_prod_brands)

        return {
            "type": "ir.actions.act_window",
            "res_model": "scrape.sparepart.dialog",
            "views": [[self.env.ref('grimm_sku.scrape_sparepart_dialog_form').id, "form"]],
            "context": {'active_model': 'product.template', 'active_ids': active_ids,
                        'default_sku_vendor_codes': sku_vendor_codes, 'default_brand': prod_brands},
            "target": "new"
        }
