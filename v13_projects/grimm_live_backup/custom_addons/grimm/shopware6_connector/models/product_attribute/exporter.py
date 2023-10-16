# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
class PropertyGroupExportMapper(Component):
    _name = 'shopware6.property.group.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.property.group']

    direct = [
        # ('technical_name', 'name'),
        ('display_in_product_filter', 'filterable'),
        ('display_on_product_detail_page', 'visibleOnProductDetailPage'),
        ('display_type', 'displayType'),
    ]

    @mapping
    def assign_sorting_type(self, record):
        return {'sortingType': 'alphanumeric'}

    @mapping
    def assign_name(self, record):
        # if record.technical_name:
        #     return {'name': record.technical_name}
        return {'name': record.name or record.technical_name}

    @mapping
    def assign_description(self, record):
        return {'description': record.shopware6_description or ''}

class PropertyGroupOptionExportMapper(Component):
    _name = 'shopware6.property.group.option.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.property.group.option']

    direct = []

    @mapping
    def assign_parent_id(self, record):
        if record.attribute_id and record.attribute_id.shopware6_bind_ids:
            return {'groupId': record.attribute_id.shopware6_bind_ids[0].shopware6_id}
        return {}

    @mapping
    def assign_name(self, record):
        return {'name': record.name[:255]} # Shopware accept only 255 character for option so trimmed it.


class Shopware6PropertyGroupExporter(Component):
    _name = 'shopware6.property.group.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.property.group']
    _usage = 'record.exporter'

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6PropertyGroupExporter, self).run(binding_id, *args, **kwargs)
        return res


    def _after_export(self):
        '''
        After export of product attribute we need to export product attribute value too.
        :return:
        '''
        for value in self.binding.openerp_id.value_ids:
            bind_value = self.binding.backend_id.create_bindings_for_model(value, 'shopware6_bind_ids')

class ShopwarePropertyGroupOptionExporter(Component):
    _name = 'shopware6.property.group.option.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.property.group.option']
    _usage = 'record.exporter'

class ProductAttributeDeleter(Component):
    _name = 'shopware6.property.group.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.property.group','shopware6.property.group.option']
    _usage = 'record.exporter.deleter'
