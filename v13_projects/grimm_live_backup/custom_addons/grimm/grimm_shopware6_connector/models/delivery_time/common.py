# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.addons.component.core import Component
import logging
from datetime import datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action


IMPORT_DELTA_BUFFER = 30


class Shopware6DeliveryTime(models.Model):
    _name = 'shopware6.delivery.time'
    _inherit = ['shopware6.binding']
    _description = 'Shopware6 Delivery Time'
    _parent_name = 'backend_id'


    name = fields.Char(required=True)
    unit = fields.Selection(string='Unit', selection=[('week', 'Week'), ('day', 'Day'), ('month', 'Month'), ('year', 'Year')],default='week')
    min = fields.Integer(string="Minimum")
    max = fields.Integer(string="Minimum")
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')

    def _get_is_shopware6_exported(self):
        self.is_shopware6_exported = False
        for this in self:
            this.is_shopware6_exported = True if this.shopware6_id else False

    def export_to_shopware6(self):
        for record in self:
            record.with_delay().export_record()
        return True

class Shopware6DeliveryTime(Component):
    _name = 'shopware6.delivery.time'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.delivery.time'

    _shopware_uri = 'api/v3/delivery-time/'

    def _call(self, method, api_call, arguments=None):
        return super(Shopware6DeliveryTime, self)._call(method, api_call, arguments)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('get','%s' % self._shopware_uri,[filters] if filters else [{}])

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('get', '%s%s' % (self._shopware_uri,id), [{}])

class GrimmShopware6DeliveryTimeListener(Component):
    _name = 'shopware6.delivery.time.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.delivery.time']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'updated_at' not in fields:
            record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        if record.shopware6_id:
            record.with_delay().export_delete_record(record.backend_id, record.shopware6_id)
