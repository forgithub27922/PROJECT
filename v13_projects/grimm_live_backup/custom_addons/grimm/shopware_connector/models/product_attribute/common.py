# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.tools.translate import _
from odoo.addons.component.core import Component

class PropertySet(models.Model):
    _inherit = 'property.set'

    shopware_binding_ids = fields.One2many('shopware.property.set', 'openerp_id', string='Shopware bindings')

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_binding_ids')
        return True

class ShopwarePropertySet(models.Model):
    _name = 'shopware.property.set'
    _description = 'Shopware Property Set'
    _inherit = 'shopware.binding'
    _inherits = {'property.set': 'openerp_id'}

    openerp_id = fields.Many2one('property.set', 'Property set', required=True, ondelete='cascade')
    #shopware_attribute_ids = fields.Many2many(
    #    comodel_name='shopware.product.attribute',
    #    compute='_compute_shopware_attribute_ids',
    #    string='Shopware attributes'
    #)

    @api.depends('openerp_id.product_attribute_ids', 'openerp_id.product_attribute_ids.shopware_binding_ids')
    def _compute_shopware_attribute_ids(self):
        for record in self:
            res = []

            for attr in record.openerp_id.product_attribute_ids:
                for attr_bind in attr.shopware_binding_ids:
                    if attr_bind.backend_id.id == record.backend_id.id:
                        res.append(attr_bind.id)

            record.shopware_attribute_ids = res

class ShopwarePropertySetAdapter(Component):
    _name = 'shopware.property.set.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.property.set'

    _shopware_uri = 'propertyGroups/'

    def write(self, id, data):
        """ Update records on the external system """
        return self._call('put',self._shopware_uri+id,  data)

    def create(self, data):
        """ Create records on the external system """
        return self._call('post', self._shopware_uri, data)

    def delete(self, id):
        """ Delete records on the external system """
        return self._call('delete', '%s%s' % (self._shopware_uri, id), [{}])

    def read(self, id, attributes=None):
        """ Delete records on the external system """
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    shopware_id = fields.Char(string='Shopware ID', readonly=True)
    filterable = fields.Boolean('Filterable')

class ShopwareBindingPropertySetListener(Component):
    _name = 'shopware.binding.property.set.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.property.set']

    '''
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if record.no_stock_sync:
            return
        inventory_fields = list(
            set(fields).intersection(self.INVENTORY_FIELDS)
        )
        if inventory_fields:
            record.with_delay(priority=20).export_inventory(
                fields=inventory_fields
            )
    '''

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class OdooPropertySetListener(Component):
    _name = 'property.set.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['property.set']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware_binding_ids:
            run_trigger = pp_bind.backend_id.check_allowed_fields(model_name=record._name, fields=fields)
            if run_trigger:
                pp_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware_binding_ids:
            target_shopware_id = getattr(binding,'shopware_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)


