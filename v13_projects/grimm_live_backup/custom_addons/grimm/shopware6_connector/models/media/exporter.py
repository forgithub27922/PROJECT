# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class MediaFolderMapper(Component):
    _name = 'shopware6.media.folder.export.mapper'
    _inherit = 'shopware6.export.mapper'
    #_apply_on = ['shopware6.product.template']
    _apply_on = ['shopware6.media.folder']

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def parent_id(self, record):
        #return {'parentId': False}
        if record.parent_id and record.parent_id.shopware6_bind_ids:
            return {'parentId': record.parent_id.shopware6_bind_ids[0].shopware6_id}

class ShopwareMediaFolderExporter(Component):
    _name = 'shopware6.media.folder.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.media.folder']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        if binding.openerp_id.parent_id:
            export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.parent_id, 'shopware6_bind_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(ShopwareMediaFolderExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        pass

class MediaFolderDeleter(Component):
    _name = 'shopware6.media.folder.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.media.folder']
    _usage = 'record.exporter.deleter'
