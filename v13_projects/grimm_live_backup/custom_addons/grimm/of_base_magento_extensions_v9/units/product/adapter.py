# -*- coding: utf-8 -*-


from odoo.addons.component.core import Component
import requests
import logging
_logger = logging.getLogger(__name__)


class ConfigurableProductAdapter(Component):
    _name = 'magento.product.template.adapter'
    _inherit = 'magento.product.product.adapter'
    _apply_on = 'magento.product.template'
    _magento_model = 'ol_catalog_product'

    def get_variants_of_configurable(self, magento_id):
        res = self._call('ol_catalog_product_link.list', [magento_id])
        return res

    def create(self, data):
        set_id = data.pop('set', None)
        product_sku = data.pop('sku', None)
        product_type = data.pop('type_id', None)
        assert set_id
        assert product_sku
        assert product_type

        return self._call('ol_catalog_product.create', [product_type, set_id, product_sku, data])


class OpenfellasProductAdapter(Component):
    _name = 'magento.product.product.adapter'
    _inherit = 'magento.product.product.adapter'
    _apply_on = 'magento.product.product'
    _magento_model = 'ol_catalog_product'

    def create(self, data):
        set_id = data.pop('set', None)
        product_sku = data.pop('sku', None)
        product_type = data.pop('type_id', None)
        assert set_id and product_sku and product_type
        res = self._call('ol_catalog_product.create', [product_type, set_id, product_sku, data])

        record = data.get("team_webhook", False)
        if record:
            message_string = "<table class='table'><tbody>"
            for k, v in record.items():
                message_string += "<tr><td><b>%s</b></td><td>%s</td></tr>" % (k, v)
            message_string += "</tbody></table>"
            team_url = self.work.collection.team_webhook_url
            data = {
                "title": "Neues Produkt im Shop:",
                "text": message_string,
                "themeColor": "00e600",
                "potentialAction": [
                    {
                        "@context": "http://schema.org",
                        "@type": "ViewAction",
                        "name": "View",
                        "target": [
                            record.get("URL")
                        ]
                    }
                ]
            }

            r = requests.post(url=team_url, json=data)
            if r.status_code == 200 and r.json() == 1:
                _logger.info("Message posted to microsoft team successfully...")

        return res

    def link_variant_to_configurable_product(self, magento_config_id, magento_variant_id, attributes):
        res = self._call('ol_catalog_product_link.assign', [magento_config_id, magento_variant_id, attributes])
        return res