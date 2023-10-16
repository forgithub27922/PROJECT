# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

class SalesChannelImportMapper(Component):
    _name = 'shopware6.sales.channel.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'sales.channel'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def set_matadata(self, record):
        res = {}
        attr = record.get("data").get("attributes")
        res["name"] = attr.get("name")
        res["shopware_currency_id"] = attr.get("currencyId")
        return res


class Shopware6SalesChannelImporter(Component):
    """ Import one Shopware Shop """

    _name = 'shopware6.sales.channel.record.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['sales.channel']
