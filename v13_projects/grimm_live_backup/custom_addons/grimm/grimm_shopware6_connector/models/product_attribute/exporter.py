# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class PropertyGroupExportMapper(Component):
    _name = 'shopware6.property.group.export.mapper'
    _inherit = 'shopware6.property.group.export.mapper'
    _apply_on = ['shopware6.property.group']

    @mapping
    def assign_sorting_type(self, record):
        return {'position': record.shopware6_position}