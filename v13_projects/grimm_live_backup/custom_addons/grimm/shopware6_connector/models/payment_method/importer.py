# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

class Shopware6PaymentModeImportMapper(Component):
    _name = 'shopware6.account.payment.mode.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.account.payment.mode'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def map_metadata(self, record):
        res = {}
        attr = record.get("data").get("attributes")
        res["name"] = attr.get("name")
        res["position"] = attr.get("position")
        res["description"] = attr.get("description") if attr.get("description") is not None else "description","No Description available."
        res["shopware6_active"] = attr.get("active")
        return res


class Shopware6PaymentModeImporter(Component):
    """ Import one Shopware Shop """

    _name = 'shopware6.account.payment.mode.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.account.payment.mode']
