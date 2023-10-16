# -*- coding: utf-8 -*-


from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class ShopwareRuleset(models.Model):
    _inherit = 'product.template'

    def set_ruleset(self, products, exec_shopware):
        ProductTemplate = self.env['product.template']
        for product in products:
            print(product.shopware_description)
            if product.ruleset_id and product.shopware_description == '<p><br></p>':
                shopware_desc = ProductTemplate.ruleset(product.ruleset_id, product.id,
                                                        product.shopware_property_ids)
                if exec_shopware:
                    print('Shop SD')
                    product.shopware_description = shopware_desc
                else:
                    print('Executing query SD')
                    query = "update product_template set shopware_description=%s where id = %s" % (
                        "'" + shopware_desc + "'", product.id)
                    self._cr.execute(query)

            if product.ruleset_id_prod and not product.prod_name:
                prod_name = ProductTemplate.ruleset(product.ruleset_id_prod, product.id, product.shopware_property_ids)

                if exec_shopware:
                    product.prod_name = prod_name
                    print('Shop PD')
                else:
                    print('Executing query PD')
                    query = "update product_template set prod_name=%s where id = %s" % (
                    "'" + prod_name + "'", product.id)
                    self._cr.execute(query)

            if product.ruleset_id_mt and not product.shopware_meta_title:
                shopware_meta_title = ProductTemplate.ruleset(product.ruleset_id_mt, product.id,
                                                              product.shopware_property_ids)

                if exec_shopware:
                    product.shopware_meta_title = shopware_meta_title
                    print('Shop MT')
                else:
                    print('Executing query MT')
                    query = "update product_template set shopware_meta_title=%s where id = %s" % (
                        "'" + shopware_meta_title + "'", product.id)
                    self._cr.execute(query)

            if product.ruleset_id_md and not product.shopware_meta_description:
                shopware_meta_description = ProductTemplate.ruleset(product.ruleset_id_md, product.id,
                                                                    product.shopware_property_ids)

                if exec_shopware:
                    product.shopware_meta_description = shopware_meta_description
                    print('Shop MD')
                else:
                    print('Executing query MD')
                    query = "update product_template set shopware_meta_description=%s where id = %s" % (
                        "'" + shopware_meta_description + "'", product.id)
                    self._cr.execute(query)

    def export_ruleset_to_shopware(self, active_ids=False, context=False):
        ProductTemplate = self.env['product.template']
        products = ProductTemplate.browse(active_ids)
        self.set_ruleset(products, False)

    @api.model
    def check_shopware_products_ruleset_from_queue(self, limit=1000, exec_shopware=False):
        ProductTemplate = self.env['product.template']
        products_queue = ProductTemplate.sudo().search(
            ['|', '|', '|', ('ruleset_id', '!=', False), ('ruleset_id_prod', '!=', False),
             ('ruleset_id_mt', '!=', False), ('ruleset_id_md', '!=', False)], limit=limit)
        self.set_ruleset(products_queue, exec_shopware)
