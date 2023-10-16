# -*- coding: utf-8 -*-

from odoo import models, api


class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'

    @api.model
    def update_products_prices(self, products, pricelist=None):
        if not pricelist:
            magento_backend = self.env['magento.backend'].search([])
            magento_backend = magento_backend[0] if magento_backend else magento_backend

            pricelist = magento_backend.default_company_id.pricelist_id if magento_backend else None
        res = super(ProductPriceHistory, self).update_products_prices(products, pricelist=pricelist)
        return res
