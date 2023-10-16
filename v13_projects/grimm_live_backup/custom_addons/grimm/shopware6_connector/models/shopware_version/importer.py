# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

class ShopImportMapper(Component):
    _name = 'shopware6.version.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.version'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ShopwareVersionImporter(Component):
    """ Import one Shopware Shop """

    _name = 'shopware6.version.record.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.version']
