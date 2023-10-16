# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class ShopwarePriceQueueExportMapper(Component):
    _name = 'shopware.price.queue.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.price.queue']

    @mapping
    def price_update(self, record):
        new_vals = {}
        shopware_user = self.env["res.users"].sudo().search([['login', '=', 'shopware@grimm-gastrobedarf.de']])
        if shopware_user:
            new_vals = {
                "prices": [
                    {
                        "customerGroupKey": 'EK',
                        "price": record.product_id.with_context({'uid':shopware_user.id}).calculated_magento_price if record.product_id.with_context({'uid':shopware_user.id}).calculated_magento_price > 0 else 0.01,
                        "from": 1,
                    }
                ]
            }
        shopware_id = False
        for bind in record.product_id.product_tmpl_id.shopware_bind_ids:
            shopware_id = bind.shopware_id
        return {'id':shopware_id,'mainDetail':new_vals} if shopware_id else {}

class ShopwarePriceQueueExporter(Component):
    _name = 'shopware.price.queue.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.price.queue']
    _usage = 'record.exporter'