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


class Shopware6Version(models.Model):
    _name = 'shopware6.version'
    _inherit = ['shopware6.binding']
    _description = 'Shopware6 Version'
    _parent_name = 'backend_id'

    _order = 'sort_order ASC, id ASC'

class Shopware6VersionAdapter(Component):
    _name = 'shopware6.version.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.version'

    _shopware6_uri = 'api/v3/_info/config'

    def get_version(self):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('GET', '%s' % (self._shopware6_uri), [{}])

    def get_currency(self):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('GET', 'api/v3/currency', [{}])