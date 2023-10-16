# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class UnitExporter(Component):
    _name = 'shopware6.unit.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.unit']
    _usage = 'record.exporter'

class Shopware6UnitDeleter(Component):
    _name = 'shopware6.unit.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.unit']
    _usage = 'record.exporter.deleter'