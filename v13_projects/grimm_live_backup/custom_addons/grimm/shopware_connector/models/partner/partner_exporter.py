# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class PartnerExportMapper(Component):
    _name = 'shopware.res.partner.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.res.partner']

    direct = [
        ('name', 'firstname'),
        ('email', 'email'),
        ('name', 'lastname'),
    ]

    @mapping
    def type_id(self, record):
        return {
            'salutation': 'mr',
            'billing':{
                'firstname':record.name,
                'lastname':record.name,
                'salutation':'mr',
                'street':record.street,
                'city':record.city,
                'zipcode':record.zip,
                'country':2
            }
        }

class ResPartnerExporter(Component):
    _name = 'shopware.res.partner.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.res.partner']
    _usage = 'record.exporter'

    def __init__(self, connector_env):
        super(ResPartnerExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.link_to_parent = False
        self.fields = None

    def _should_import(self):
        return False

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(ResPartnerExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        pass

class ResPartnerDeleter(Component):
    _name = 'shopware.res.partner.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.res.partner']
    _usage = 'record.exporter.deleter'

class ShopwarePartnerListener(Component):
    _name = 'shopware.binding.res.partner.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.res.partner']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()


class OdooResPartnertListener(Component):
    _name = 'res.partner.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['res.partner']

    '''
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware_bind_ids:
            pp_bind.with_delay().export_record(fields=fields)
        for pp_bind in record.shopware_supplier_ids:
            pp_bind.with_delay().export_record(fields=fields)
    

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware_bind_ids:
            target_odoo_partner_id = getattr(binding,'odoo_id')
            if target_odoo_partner_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_odoo_partner_id)
    '''



class SupplierExportMapper(Component):
    _name = 'shopware.supplier.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.supplier']

    direct = [
        ('name', 'name'),
    ]

class SupplierExporter(Component):
    _name = 'shopware.supplier.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.supplier']
    _usage = 'record.exporter'

class SupplierDeleter(Component):
    _name = 'shopware.supplier.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.supplier']
    _usage = 'record.exporter.deleter'

class ShopwareSupplierListener(Component):
    _name = 'shopware.binding.supplier.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.supplier']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()

