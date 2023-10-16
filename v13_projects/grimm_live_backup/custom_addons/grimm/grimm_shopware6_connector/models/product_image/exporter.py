# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
import logging
_logger = logging.getLogger(__name__)

class ProductImageExportMapper(Component):
    _inherit = 'shopware.product.image.export.mapper'
    _apply_on = ['shopware.product.image']

    @mapping
    def mapping_image(selfself, record):
        if record.product_tmpl_id.is_device and record.product_tmpl_id.image_ids and not record.product_tmpl_id.is_image_on_server:
            if record.file_select == 'upload':
                return {
                    "file": "data:image/jpeg;base64," + (
                        record.magento_image_id.manual_image_data if record.magento_image_id else record.image).decode(
                        "utf-8"),
                }
        else:
            if record.file_select == 'url' and record.file_url:
                return {
                    "file": record.file_url,
                }
            elif record.file_select == 'upload' and record.image:
                return {
                    "file": "data:image/jpeg;base64,"+(record.image).decode("utf-8"),
                }

