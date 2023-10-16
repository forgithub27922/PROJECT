# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


from odoo.addons.shopware_connector.components.binder import ShopwareModelBinder

class GrimmShopwareModelBinder(ShopwareModelBinder):
    _apply_on = ShopwareModelBinder._apply_on + [
        'shopware.brand',
        'shopware.price.queue',
    ]
