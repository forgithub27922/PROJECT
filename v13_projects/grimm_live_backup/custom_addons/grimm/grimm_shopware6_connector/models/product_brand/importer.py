# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError

class Shopware6GrimmProductBrandImporter(Component):
    _name = 'shopware6.brand.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.grimm.product.brand']

class Shopware6GrimmProductBrandImportMapper(Component):
    _name = 'shopware6.brand.import.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.grimm.product.brand'