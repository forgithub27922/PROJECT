# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class Shopware6DocumentTypeExportMapper(Component):
    _name = 'shopware6.document.type.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.document.type']

    direct = [
        ('name', 'name'),
        ('technical_name', 'technical_name'),
    ]

class Shopware6DocumentExportMapper(Component):
    _name = 'shopware6.document.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.document']

    @mapping
    def assign_meta_data(self, record):
        data = {"config": {"custom": {"invoiceNumber": record.doc_number}, "documentNumber": record.doc_number,
                           "documentComment": record.doc_comment}, "static": True, "shopware6_id":record.order_id, "doc_type":record.doc_type}
        return data

class DocumentTypeExporter(Component):
    _name = 'shopware6.document.type.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.document.type']
    _usage = 'record.exporter'

class DocumentExporter(Component):
    _name = 'shopware6.document.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.document']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        need_to_delete = self.env["shopware6.document"].search([('doc_type', '=', 'invoice'), ('order_id', '=', binding.order_id),('id', '!=', binding.id),('shopware6_id', '!=', False)])
        for document in need_to_delete:
            self.backend_adapter.delete(document.shopware6_id)
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(DocumentExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        if self.binding.shopware6_id:
            upload_file = self.backend_adapter.upload_file(self.binding)
        pass

class DocumentTypeDeleter(Component):
    _name = 'shopware6.document.type.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.document.type','shopware6.document']
    _usage = 'record.exporter.deleter'