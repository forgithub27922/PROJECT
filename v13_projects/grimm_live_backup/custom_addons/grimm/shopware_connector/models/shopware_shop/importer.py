# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

class ShopImportMapper(Component):
    _name = 'shopware.shop.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.shop'

    direct = [('name', 'name'),
              ('templateId', 'template_id'),
              ('host', 'host'),
              ('active', 'enabled'),
              ('secure', 'secure'),
              ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ShopwareShopImporter(Component):
    """ Import one Shopware Shop """

    _name = 'shopware.shop.record.importer'
    _inherit = 'shopware.importer'
    _apply_on = ['shopware.shop']
