# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ShopwareModelBinder(Component):
    """ Bind records and give odoo/Shopware ids correspondence

    Binding models are models called ``shopware.{normal_model}``,
    like ``shopware.res.partner`` or ``shopware.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Shopware ID, the ID of the Shopware Backend and the additional
    fields belonging to the Shopware instance.
    """
    _name = 'shopware.binder'
    _inherit = ['base.binder', 'base.shopware.connector']
    _apply_on = [
        'shopware.res.partner',
        'shopware.address',
        'shopware.invoice.address',
        'shopware.product.template',
        'shopware.product.product',
        'shopware.product.category',
        'shopware.product.image',
        'shopware.image.info',
        'shopware.supplier',
        'shopware.shop',
        'shopware.sale.order',
        'shopware.sale.order.line',
        'shopware.property.set',
    ]

    _external_field = 'shopware_id'
    _odoo_field = 'openerp_id'

    def to_openerp(self, external_id, unwrap=False):
        super(ShopwareModelBinder, self).to_internal(external_id, unwrap=unwrap)
