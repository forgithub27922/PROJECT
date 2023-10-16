# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class ProductCategoryMapper(Component):
    _name = 'shopware.product.category.export.mapper'
    _inherit = 'shopware.export.mapper'
    #_apply_on = ['shopware.product.template']
    _apply_on = ['shopware.product.category']

    direct = [
        ('name', 'name')
    ]

    @mapping
    def parent_id(self, record):
        if record.parent_id.shopware_bind_ids:
            return {'parentId': record.parent_id.shopware_bind_ids[0].shopware_id}

class ShopwareProductCategoryExporter(Component):
    _name = 'shopware.product.category.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.product.category']
    _usage = 'record.exporter'

    def __init__(self, connector_env):
        super(ShopwareProductCategoryExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.link_to_parent = False
        self.fields = None

    def _should_import(self):
        return False

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(ShopwareProductCategoryExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        pass

class ProductCategoryDeleter(Component):
    _name = 'shopware.product.category.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.product.category']
    _usage = 'record.exporter.deleter'
