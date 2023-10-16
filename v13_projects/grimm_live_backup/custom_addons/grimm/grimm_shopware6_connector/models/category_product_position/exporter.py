# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
import uuid
import logging
_logger = logging.getLogger(__name__)

class CategoryRelatedProductExportMapper(Component):
    _name = 'category.related.product.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['category.related.product']

    def get_shopware6_id(self,product_id):
        if product_id._name in ['product.product', 'product.category']:
            for bind in product_id.shopware6_bind_ids:
                return bind.shopware6_id if bind.shopware6_id else False
        if product_id._name in ['product.template']:
            for bind in product_id.shopware6_pt_bind_ids:
                return bind.shopware6_id if bind.shopware6_id else False

    @mapping
    def assign_position(self, record):
        res = {}
        compute_field = record.category_id.compute_field
        items = []
        category_shopware6_id = self.get_shopware6_id(record.category_id)
        category_adapter = self.component(usage='backend.adapter', model_name='shopware6.product.category')
        category_data = category_adapter.read(category_shopware6_id)
        category_varsion_id = category_data.get("attributes",{}).get("versionId", False)
        if category_varsion_id:
            for product in record.category_id.related_product_ids:
                if product.product_id:
                    shopware6_id = self.get_shopware6_id(product.product_id)
                if product.product_tmpl_id:
                    shopware6_id = self.get_shopware6_id(product.product_tmpl_id)
                if shopware6_id:
                    items.append({"id":shopware6_id, "position":int(product.sequence + 1000), "version_id": category_varsion_id})
            res["items"] = items
            res["categoryId"] = category_shopware6_id
            res["categoryVersionId"] = category_varsion_id
        return res

class CategoryRelatedProductExporter(Component):
    _name = 'category.related.product.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['category.related.product']
    _usage = 'record.exporter'