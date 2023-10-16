# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
import logging
_logger = logging.getLogger(__name__)

class AccessoryPartProductMapperShopware6(Component):
    _name = 'shopware6.accessory.part.product.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.accessory.part.product']

    @mapping
    def assign_accessory_part_id(self, record):
        return_dict = {}
        shopware6_id = False
        if record.accessory_part_id.product_variant_count == 1:
            for bind in record.accessory_part_id.shopware6_bind_ids:
                shopware6_id = bind.shopware6_id if bind.shopware6_id else False
        else:
            for bind in record.accessory_part_id.shopware6_pt_bind_ids:
                shopware6_id = bind.shopware6_id if bind.shopware6_id else False
        if shopware6_id:
            return_dict["productId"] = shopware6_id

        return_dict["crossSellingId"] = record.product_id.cross_selling_id
        return_dict["position"] = record.sequence
        return return_dict

class Shopware6AccessoryPartProductExporter(Component):
    _name = 'shopware6.accessory.part.product.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.accessory.part.product']
    _usage = 'record.exporter'

class Shopware6AccessoryPartProductDeleter(Component):
    _name = 'shopware6.accessory.part.product.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.accessory.part.product']
    _usage = 'record.exporter.deleter'

