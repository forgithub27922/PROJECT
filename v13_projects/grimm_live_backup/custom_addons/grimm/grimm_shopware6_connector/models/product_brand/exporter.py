# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class GrimmShopware6ProductBrandExportMapper(Component):
    _name = 'shopware6.grimm.product.brand.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.grimm.product.brand']

    direct = [
        ('name', 'name'),
    ]

class GrimmProductBrandExporter(Component):
    _name = 'shopware6.brand.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.grimm.product.brand']
    _usage = 'record.exporter'

class GrimmProductBrandDeleter(Component):
    _name = 'shopware6.grimm.product.brand.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.grimm.product.brand']
    _usage = 'record.exporter.deleter'