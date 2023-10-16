# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
import logging
_logger = logging.getLogger(__name__)

class Shopware6MediaManagerMapper(Component):
    _name = 'shopware6.media.manager.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.media.manager']

    @mapping
    def assign_meta_data(self, record):
        return_dict = {}
        return_dict["title"] = record.name
        return return_dict

    @changed_by('media_url')
    @mapping
    def assign_custom_fields(self, record):
        return_dict = {}
        if record.media_url:
            return_dict["grimm_media_src"] = record.media_url
        if return_dict:
            return {"customFields": return_dict}
        return return_dict

    @mapping
    def assign_folder(self, record):
        return_dict = {}
        if record.backend_id.default_media_folder_id:
            return_dict["mediaFolderId"] = record.backend_id.default_media_folder_id.shopware6_bind_ids[0].shopware6_id
        return return_dict

class Shopware6MediaManagerExporter(Component):
    _name = 'shopware6.media.manager.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.media.manager']
    _usage = 'record.exporter'

    def _get_shopware6_id(self, product):
        shopware6_id = False
        for binding in product.shopware6_bind_ids:
            shopware6_id = self.binder.to_external(binding)
        return shopware6_id

    def _after_export(self):
        res = super(Shopware6MediaManagerExporter, self)._after_export()
        config_setting = self.backend_adapter.set_image(self.binding)

        shopware6_media_product = {}
        odoo_shopware6_ids = []
        need_to_delete = []
        need_to_create = []

        for product in self.binding.product_ids:
            shopware6_id = self._get_shopware6_id(product)
            if shopware6_id:
                odoo_shopware6_ids.append(shopware6_id)

        product_media = self.backend_adapter.get_assigned_products(self.binding.shopware6_id)
        for p_media in product_media:
            attr = p_media.get("attributes")
            shopware6_media_product[p_media.get("id")] = attr.get("productId")

        for k,v in shopware6_media_product.items():
            if v not in odoo_shopware6_ids:
                need_to_delete.append(k)

        for odoo_id in odoo_shopware6_ids:
            if odoo_id not in shopware6_media_product.values():
                need_to_create.append(odoo_id)
        for remove in need_to_delete:
            product_adapter_media = self.component(usage='backend.adapter',model_name='shopware6.product.media')
            deleted = product_adapter_media.delete(remove)
        max_index = 9999
        for add in need_to_create:
            self.backend_adapter.create_product_media({"mediaId":self.binding.shopware6_id, 'productId':add, 'position': max_index})
            max_index += 1
        return res

class Shopware6MediaManagerDeleter(Component):
    _name = 'shopware6.media.manager.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.media.manager']
    _usage = 'record.exporter.deleter'

