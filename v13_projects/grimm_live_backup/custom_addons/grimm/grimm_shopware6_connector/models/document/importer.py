# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class Shopware6DocumentTypeBatchImporter(Component):
    """ Import the Shopware Document Type.
    """
    _name = 'shopware6.document.type.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.document.type']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        shopware6_ids = self.backend_adapter.search(filters)
        for shopware6_id in shopware6_ids.get("data"):
            shopware_sale_id = shopware6_id.get('id')
            self._import_record(shopware_sale_id)

class Shopware6DocumentType(Component):
    _name = 'shopware6.document.type.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.document.type'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def set_matadata(self, record):
        res = {}
        attr = record.get("data").get("attributes")
        res["name"] = attr.get("name")
        res["technical_name"] = attr.get("technical_name")
        return res


class Shopware6DocumentTypeImporter(Component):
    """ Import one Shopware Document Type """

    _name = 'shopware6.document.type.record.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.document.type']
