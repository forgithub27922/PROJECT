# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


class ProductMediaBatchImporter(Component):
    """ Import the Shopware6 product media.
    """
    _name = 'shopware6.product.media.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.product.media','shopware6.product.media.file']

class ProductMediaImporter(Component):
    _name = 'shopware6.product.media.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.product.media','shopware6.product.media.file']

