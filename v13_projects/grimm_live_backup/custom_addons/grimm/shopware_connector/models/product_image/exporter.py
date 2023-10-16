# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
class ProductImageExportMapper(Component):
    _name = 'shopware.product.image.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.product.image']

    direct = [
        ('name', 'description'),
    ]

    @mapping
    def mapping_album(selfself, record):
        return {
            "album": -1,
            "type": "IMAGE",
        }

    @mapping
    def mapping_image(selfself, record):
        if record.file_select == 'url' and record.file_url:
            return {
                "file": record.file_url,
            }
        elif record.file_select == 'upload' and record.image:
            return {
                "file": "data:image/jpeg;base64,"+(record.image).decode("utf-8"),
            }


class ShopwareProductImageExporter(Component):
    _name = 'shopware.product.image.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.product.image']
    _usage = 'record.exporter'


class ProductDeleter(Component):
    _name = 'shopware.product.image.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.product.image']
    _usage = 'record.exporter.deleter'
