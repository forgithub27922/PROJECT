# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


class Shopware6ProductProductImporter(Component):
    _name = 'shopware6.product.product.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.product.product','shopware6.image.info']


class Shopware6ProductProductImportMapper(Component):
    _name = 'shopware6.product.product.import.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.product.product'