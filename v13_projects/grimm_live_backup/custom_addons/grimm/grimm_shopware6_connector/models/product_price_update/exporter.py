# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class Shopware6PriceQueueExportMapper(Component):
    _name = 'shopware6.price.queue.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.price.queue']

    @mapping
    def price_update(self, record):
        product_mapper = self.component(usage='export.mapper', model_name='shopware6.product.product')
        res = {}
        for binding in record.product_id.shopware6_bind_ids:
            res["data"] = product_mapper.assign_price(binding)
            res["id"] = binding.shopware6_id
        return res

class Shopware6PriceQueueExporter(Component):
    _name = 'shopware6.price.queue.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.price.queue']
    _usage = 'record.exporter'