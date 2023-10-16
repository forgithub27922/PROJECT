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

class Shopware6PropertyGroup(models.Model):
    _name = 'shopware6.property.group'
    _description = 'Shopware6 Property Group'
    _inherit = 'shopware6.binding'
    _inherits = {'product.attribute': 'openerp_id'}

    openerp_id = fields.Many2one('product.attribute', 'Attribute', required=True, ondelete='cascade')
    #shopware_attribute_ids = fields.Many2many(
    #    comodel_name='shopware6.product.attribute',
    #    compute='_compute_shopware_attribute_ids',
    #    string='Shopware attributes'
    #)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export Property Group record to Shopware 6"""
        return super(Shopware6PropertyGroup, self).export_record(fields)

class Shopware6PropertyGroupOption(models.Model):
    _name = 'shopware6.property.group.option'
    _description = 'Shopware6 Property Group Option'
    _inherit = 'shopware6.binding'
    _inherits = {'product.attribute.value': 'openerp_id'}

    openerp_id = fields.Many2one('product.attribute.value', 'Attribute Value', required=True, ondelete='cascade')
    #shopware_attribute_ids = fields.Many2many(
    #    comodel_name='shopware6.product.attribute',
    #    compute='_compute_shopware_attribute_ids',
    #    string='Shopware attributes'
    #)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export Property Group Option record to Shopware 6"""
        return super(Shopware6PropertyGroupOption, self).export_record(fields)

class Shopware6PropertyGroupAdapter(Component):
    _name = 'shopware6.property.group.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.property.group'

    _shopware_uri = 'api/v3/property-group/'

class Shopware6PropertyGroupOptionAdapter(Component):
    _name = 'shopware6.property.group.option.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.property.group.option'

    _shopware_uri = 'api/v3/property-group-option/'



class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.property.group',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')
    display_in_product_filter = fields.Boolean(string="Shopware6 Product Filter")
    display_on_product_detail_page = fields.Boolean(string="Shopware6 Product Detail Page")
    shopware6_description = fields.Text(string="Shopware6 Description")
    display_type = fields.Selection(string='Display Type', selection=[('text', 'Text'),('select', 'Select')], default='text')

    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True

    def export_to_shopware6(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.property.group.option',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')

    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True

class Shopware6PropertyGroupListener(Component):
    _name = 'shopware6.property.group.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.property.group', 'shopware6.property.group.option']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()

class OdooProductAttributeListener(Component):
    _name = 'product.attribute.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.attribute']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for bind in record.shopware6_bind_ids:
            bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding,'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)

class OdooProductAttributeValueListener(Component):
    _name = 'product.attribute.value.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.attribute.value']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for bind in record.shopware6_bind_ids:
            bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        for bind in record.attribute_id.shopware6_bind_ids:
            export_property_value = bind.backend_id.create_bindings_for_model(record, 'shopware6_bind_ids')

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding,'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)