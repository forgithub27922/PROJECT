# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class ProductCategoryMapperShopware6(Component):
    _name = 'shopware6.product.category.export.mapper'
    _inherit = 'shopware6.export.mapper'
    #_apply_on = ['shopware.product.template']
    _apply_on = ['shopware6.product.category']

    direct = [
        ('name', 'name'),
    ]

    @changed_by('shopware6_meta_title', 'shopware6_meta_description', 'shopware6_meta_keywords')
    @mapping
    def set_meta_info(self, record):
        meta_info = {}
        meta_info["metaTitle"] = record.shopware6_meta_title or ""
        meta_info["metaDescription"] = record.shopware6_meta_description or ""
        meta_info["keywords"] = record.shopware6_meta_keywords or ""
        return meta_info

    @mapping
    def map_info(self, record):
        meta_info = {}
        meta_info["active"] = record.shopware6_active
        meta_info["visible"] = record.shopware6_active
        meta_info["type"] = record.shopware6_category_type
        meta_info["productAssignmentType"] = record.shopware6_category_assignment_type
        meta_info["description"] = record.shopware6_description or ""
        return meta_info

    @mapping
    def parent_id(self, record):
        #return {'parentId': False}
        if record.parent_id and record.parent_id.shopware6_bind_ids:
            return {'parentId': record.parent_id.shopware6_bind_ids[0].shopware6_id}

class Shopware6ProductCategoryExporter(Component):
    _name = 'shopware6.product.category.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.product.category']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        if binding.openerp_id.parent_id:
            export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.parent_id, 'shopware6_bind_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6ProductCategoryExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        pass

class ProductCategoryDeleterShopware6(Component):
    _name = 'shopware6.product.category.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.product.category']
    _usage = 'record.exporter.deleter'
