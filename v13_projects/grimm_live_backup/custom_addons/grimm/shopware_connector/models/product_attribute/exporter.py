# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
class PropertySetExportMapper(Component):
    _name = 'shopware.property.set.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.property.set']

    direct = [
        ('name', 'name'),
        ('position', 'position'),
        ('comparable', 'comparable'),
        ('sort_mode', 'sortMode'),
    ]

    @mapping
    def assign_option(self, record):
        return {'name': record.name, 'position': record.position, 'sortMode': record.sort_mode,
                'comparable': record.comparable}
    #   option_list = []
    #    for attr in record.product_attribute_ids:
    #        if not attr.shopware_id:
    #            option_list.append({"name": attr.name})
    #    return {'options':option_list} if option_list else {}

class ShopwarePropertySetExporter(Component):
    _name = 'shopware.property.set.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.property.set']
    _usage = 'record.exporter'

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(ShopwarePropertySetExporter, self).run(binding_id, *args, **kwargs)
        return res


    def _after_export(self):
        '''
        This method will again execute read method for same Property Set because we need image link ID from shopware
        so product will not add images with every request.
        :return:
        '''
        set_data = self.backend_adapter.read(int(self.binding.shopware_id))
        image_data = set_data.get('options')
        set_link = {}
        for set in image_data:
            set_link[str(set.get('name'))] = set.get('id')
        set_id = self.binding.openerp_id
        for attribute in set_id.product_attribute_ids:
            shopware_id = set_link.get(attribute.with_context(lang=self.env.user.lang).name,False)
            if not shopware_id:
                shopware_id = set_link.get(attribute.with_context(lang='en_US').name, False)
            if int(attribute.shopware_id) < 1 and shopware_id:
                self.env.cr.execute("update product_attribute set shopware_id=%s where id=%s;",(int(shopware_id),int(attribute.id),))




class ProductDeleter(Component):
    _name = 'shopware.property.set.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.property.set']
    _usage = 'record.exporter.deleter'
