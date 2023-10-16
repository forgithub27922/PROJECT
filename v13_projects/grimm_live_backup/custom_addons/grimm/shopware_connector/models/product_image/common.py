# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client

from collections import defaultdict

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in range(0, len(items), length):
        yield items[index:index + length]

class OdooProductImage(models.Model):
    _name = 'odoo.product.image'
    _description = 'Odoo Product Image'
    _order = 'position'

    @api.model
    def select_image_upload_options(self):
        return [('upload', 'Upload File'),('url', 'URL')]

    #product_tmpl_id = fields.Many2one('product.template', string='Standalone product', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', string='Variant product', ondelete='cascade')

    name = fields.Char('Name', required=True)
    file_name = fields.Char('File Name')
    file_select = fields.Selection(string='Upload Option', selection='select_image_upload_options', required=True, default='upload')
    file_url = fields.Char('File URL')
    position = fields.Integer(string='Position', store=True)
    image = fields.Binary("Shopware Image", attachment=True,help="Shopware Image.", )
    shopware_id = fields.Integer(string="Shopware ID",readonly=True)

    shopware_bind_ids = fields.One2many(
        comodel_name='shopware.product.image',
        inverse_name='openerp_id',
        string='Shopware Bindings',
    )

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_bind_ids')
        return True


class ShopwareProductImage(models.Model):
    _name = 'shopware.product.image'
    _inherit = 'shopware.binding'
    _inherits = {'odoo.product.image': 'openerp_id'}
    _description = 'Shopware Product'


    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')

    openerp_id = fields.Many2one(comodel_name='odoo.product.image',
                                 string='Product Image',
                                 required=True,
                                 ondelete='cascade')
    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Product to Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class ShopwareProductImageAdapter(Component):
    _name = 'shopware.product.image.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.product.image'

    _shopware_uri = 'media/'

    def write(self, id, data):
        """ Update product image records on the external system """
        return self._call('put',self._shopware_uri+id,  data)

    def create(self, data):
        """ create product image records on the external system """
        return self._call('post', self._shopware_uri, data)

    def delete(self, id):
        """ Delete product image records on the external system """
        return self._call('delete', '%s%s' % (self._shopware_uri, id), [{}])

    def read(self, id, attributes=None):
        """ Read product image records on the external system """
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

class ShopwareBindingProductImageListener(Component):
    _name = 'shopware.binding.product.image.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.product.image']

    # fields which should not trigger an export of the products
    # but an export of their inventory
    INVENTORY_FIELDS = ('manage_stock',
                        'backorders',
                        'shopware_qty',
                        )
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        run_trigger = record.check_allowed_fields(model_name=record._name, fields=fields)
        if run_trigger:
            if record.no_stock_sync:
                return
            inventory_fields = list(
                set(fields).intersection(self.INVENTORY_FIELDS)
            )
            if inventory_fields:
                record.with_delay(priority=20).export_inventory(
                    fields=inventory_fields
                )

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()


class OdooProductImageListener(Component):
    _name = 'odoo.product.image.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['odoo.product.image']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware_bind_ids:
            run_trigger = pp_bind.backend_id.check_allowed_fields(model_name=record._name, fields=fields)
            if run_trigger:
                pp_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware_bind_ids:
            binding.with_delay().export_delete_record(binding.backend_id, binding.shopware_id)
