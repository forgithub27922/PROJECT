# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class Shopware6DeliveryTimeBatchImporter(Component):
    """ Import the Shopware Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware6.delivery.time.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.delivery.time']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        shopware6_ids = self.backend_adapter.search(filters)
        for shopware6_id in shopware6_ids.get("data"):
            shopware_sale_id = shopware6_id.get('id')
            self._import_record(shopware_sale_id)

class Shopware6DeliveryTime(Component):
    _name = 'shopware6.delivery.time.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.delivery.time'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def set_matadata(self, record):
        res = {}
        attr = record.get("data").get("attributes")
        res["name"] = attr.get("name")
        res["min"] = attr.get("min")
        res["max"] = attr.get("max")
        res["unit"] = attr.get("unit")
        return res


class Shopware6DeliveryTimeImporter(Component):
    """ Import one Shopware Shop """

    _name = 'shopware6.delivery.time.record.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.delivery.time']
