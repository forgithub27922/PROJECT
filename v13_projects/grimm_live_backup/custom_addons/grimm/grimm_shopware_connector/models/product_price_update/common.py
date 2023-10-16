# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

class ShopwarePriceQueue(models.Model):
    """ Binding Model for the Odoo Res Partner """
    _name = 'shopware.price.queue'
    _inherit = 'shopware.binding'
    _inherits = {'shopware.product.update.queue': 'openerp_id'}
    _description = 'Shopware Price'

    openerp_id = fields.Many2one(comodel_name='shopware.product.update.queue',
                              string='Price Update Queue',
                              required=True,
                              ondelete='cascade')

    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')

    @job(default_channel='root.shopware')
    @related_action(action='Shopware Price Update Trigger')
    def shopware_price_trigger(self, fields=None):
        """ Price Trigger on Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class ShopwarePriceQueueAdapter(Component):
    _name = 'shopware.price.queue.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.price.queue'

    _shopware_uri = 'articles/'

    def create(self, data):
        """ Update price on the Shopware system """
        return self._call('put', '%s%s' % (self._shopware_uri, data.get("id")), data)

class ShopwareBindingPriceQueueListener(Component):
    _name = 'shopware.binding.price.queue.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.price.queue']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().shopware_price_trigger()