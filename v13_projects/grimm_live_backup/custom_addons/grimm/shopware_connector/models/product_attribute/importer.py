# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


class PropertySetImporter(Component):
    _name = 'shopware.property.set.importer'
    _inherit = 'shopware.importer'
    _apply_on = ['shopware.property.set']


class PropertySetImportMapper(Component):
    _name = 'shopware.property.set.import.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.property.set'