# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import AbstractComponent


class BaseShopware6ConnectorComponent(AbstractComponent):
    """ Base Shopware Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.shopware6.connector'
    _inherit = 'base.connector'
    _collection = 'shopware6.backend'