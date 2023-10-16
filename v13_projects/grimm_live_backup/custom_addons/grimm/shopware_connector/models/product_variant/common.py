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

class ShopwareProductProduct(models.Model):
    _name = 'shopware.product.product'
    _inherit = 'shopware.binding'
    _inherits = {'product.product': 'openerp_id'}
    _description = 'Shopware Product'


    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')

    openerp_id = fields.Many2one(comodel_name='product.product',
                                 string='Product',
                                 required=True,
                                 ondelete='cascade')
    shopware_created_at = fields.Date('Created At (on Shopware)')
    shopware_updated_at = fields.Date('Updated At (on Shopware)')

    shopware_qty = fields.Float(string='Computed Quantity',
                               help="Last computed quantity to send "
                                    "on Shopware.")
    no_stock_sync = fields.Boolean(
        string='No Stock Synchronization',
        required=False,
        help="Check this to exclude the product "
             "from stock synchronizations.",
    )

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Product to Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopware_variant_bind_ids = fields.One2many(
        comodel_name='shopware.product.product',
        inverse_name='openerp_id',
        string='Shopware Bindings',
    )


    #status_on_shopware = fields.Boolean(string="Status on Shopware")
    #shopware_meta_title = fields.Char(string='Meta Title', copy=True)
    #shopware_meta_keyword = fields.Text(string='Meta Keyword', copy=True)
    #shopware_meta_description = fields.Text(string='Meta Description', copy=True)
    #shopware_variant_image_ids = fields.One2many(
    #    comodel_name='odoo.product.image',
    #    inverse_name='product_id',
    #    string='Shopware Images',
    #)

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_bind_ids')
        return True


class ProductProductAdapter(Component):
    _name = 'shopware.product.product.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.product.product'

    _shopware_uri = 'variants/'

    def read(self, id, attributes=None):
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update records on the external shopware system """
        return self._call('put',self._shopware_uri+id,  data)

    def create(self, data):
        """ Create records on the external shopware system """
        return self._call('post', self._shopware_uri, data)

    def delete(self, id):
        """ Delete records on the external shopware system """
        return self._call('delete',self._shopware_uri+id)

class ShopwareBindingProductListener(Component):
    _name = 'shopware.binding.product.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.product.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class OdooProductListener(Component):
    _name = 'product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.product']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware_bind_ids:
            run_trigger = pp_bind.backend_id.check_allowed_fields(model_name=record._name, fields=fields)
            if run_trigger:
                pp_bind.with_delay().export_record(fields=fields)