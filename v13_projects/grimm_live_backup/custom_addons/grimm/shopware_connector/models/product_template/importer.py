# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


class ProductTemplateImporter(Component):
    _name = 'shopware.product.template.importer'
    _inherit = 'shopware.importer'
    _apply_on = ['shopware.product.template','shopware.image.info']


class ProductTemplateImportMapper(Component):
    _name = 'shopware.product.template.import.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.product.template'

class ShopwareImageInfoImportMapper(Component):
    _name = 'shopware.image.info.import.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.image.info'

class OdooProductImageImportMapper(Component):
    _name = 'odoo.product.image.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'odoo.product.image'

