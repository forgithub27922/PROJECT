# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import uuid
from odoo import models, fields, api
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

class Shopware6PriceQueue(models.Model):
    """ Binding Model for the Odoo Res Partner """
    _name = 'shopware6.price.queue'
    _inherit = 'shopware6.binding'
    _inherits = {'shopware6.product.update.queue': 'openerp_id'}
    _description = 'Shopware Price'

    openerp_id = fields.Many2one(comodel_name='shopware6.product.update.queue',
                              string='Price Update Queue',
                              required=True,
                              ondelete='cascade')

    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')



class Shopware6PriceQueueAdapter(Component):
    _name = 'shopware6.price.queue.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.price.queue'

    _shopware_uri = 'api/v3/product/'

    def create(self, data):
        """ Update price on the Shopware system """
        self._call('PATCH', '%s%s' % (self._shopware_uri, data.get("id")), data.get("data"))
        return uuid.uuid1()

class Shopware6BindingPriceQueueListener(Component):
    _name = 'shopware.binding.price.queue.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.price.queue']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()