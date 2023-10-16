# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import AbstractComponent


class BaseShopwareConnectorComponent(AbstractComponent):
    """ Base Shopware Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.shopware.connector'
    _inherit = 'base.connector'
    _collection = 'shopware.backend'