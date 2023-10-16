# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class BrandExportMapper(Component):
    _name = 'shopware.brand.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.brand']

    direct = [
        ('name', 'name'),
    ]

class BrandExporter(Component):
    _name = 'shopware.brand.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.brand']
    _usage = 'record.exporter'

class BrandDeleter(Component):
    _name = 'shopware.brand.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.brand']
    _usage = 'record.exporter.deleter'

class ShopwareBrandListener(Component):
    _name = 'shopware.binding.brand.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.brand']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()