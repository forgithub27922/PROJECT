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

IMPORT_DELTA_BUFFER = 30


class Shopware6Tax(models.Model):
    _name = 'shopware6.tax'
    _inherit = ['shopware6.binding']
    _description = 'Shopware Taxes'
    _parent_name = 'backend_id'


    name = fields.Char(required=True, readonly=True)
    tax_rate = fields.Float(readonly=True)
    odoo_tax_id = fields.Many2one(comodel_name='account.tax', string='Odoo Tax')


class Shopware6TaxAdapter(Component):
    _name = 'shopware6.tax.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.tax'

    _shopware_uri = 'api/v3/tax/'

    def _call(self, method, api_call, arguments=None):
        return super(Shopware6TaxAdapter, self)._call(method, api_call, arguments)

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
