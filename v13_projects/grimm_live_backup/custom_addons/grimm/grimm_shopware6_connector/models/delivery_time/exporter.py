# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class Shopware6DeliveryTimeExportMapper(Component):
    _name = 'shopware6.delivery.time.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.delivery.time']

    direct = [
        ('name', 'name'),
        ('unit', 'unit'),
    ]

    @mapping
    def map_min_max_value(self, record):
        res = {}
        res["min"] = record.min or 0
        res["max"] = record.max or 0
        return res

class DeliveryTimeExporter(Component):
    _name = 'shopware6.delivery.time.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.delivery.time']
    _usage = 'record.exporter'

class DeliveryTimeDeleter(Component):
    _name = 'shopware6.delivery.time.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.delivery.time']
    _usage = 'record.exporter.deleter'