# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class Shopware6UnitImporter(Component):
    """ Import the Shopware6 Units.

    For every Unit in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware6.unit.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.unit']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        shopware6_ids = self.backend_adapter.search(filters)
        total_shopware6_units = []
        for shopware6_id in shopware6_ids.get("data"):
            shopware6_unit_id = shopware6_id.get('id')
            total_shopware6_units.append(shopware6_unit_id)
            self._import_record(shopware6_unit_id)
        total_shopware6_units = tuple(total_shopware6_units)
        self.env.cr.execute("delete from shopware6_unit where shopware6_id not in %s" % str(total_shopware6_units))


class Shopware6UnitImportMapper(Component):
    _name = 'shopware6.unit.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.unit'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def set_matadata(self, record):
        res = {}
        attr = record.get("data").get("attributes")
        res["name"] = attr.get("name")
        res["shortCode"] = attr.get("shortCode")
        return res


class Shopware6UnitImporter(Component):
    """ Import one Shopware6 Unit """

    _name = 'shopware6.unit.record.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.unit']

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        #binding.openerp_id.get_delivery_price()
        #binding.openerp_id.set_delivery_line()
        record = super(Shopware6UnitImporter, self)._after_import(binding)
        return record
