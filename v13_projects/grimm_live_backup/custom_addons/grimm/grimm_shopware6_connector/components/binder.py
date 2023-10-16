# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


from odoo.addons.shopware6_connector.components.binder import Shopware6ModelBinder

class GrimmShopwareModelBinder(Shopware6ModelBinder):
    _apply_on = Shopware6ModelBinder._apply_on + [
        'shopware6.grimm_custom_product.template',
        'shopware6.grimm_custom_product.option',
        'shopware6.grimm_custom_product.option_value',
        'shopware6.grimm.product.brand',
        'shopware6.accessory.part.product',
        'shopware6.delivery.time',
        'shopware6.media.manager',
        'shopware6.price.queue',
        'shopware6.document.type',
        'shopware6.document',
        'category.related.product',
        'shopware6.unit',
    ]