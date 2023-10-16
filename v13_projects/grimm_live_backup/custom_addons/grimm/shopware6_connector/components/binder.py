# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class Shopware6ModelBinder(Component):
    """ Bind records and give odoo/Shopware6 ids correspondence

    Binding models are models called ``shopware6.{normal_model}``,
    like ``shopware6.res.partner`` or ``shopware6.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Shopware6 ID, the ID of the Shopware6 Backend and the additional
    fields belonging to the Shopware6 instance.
    """
    _name = 'shopware6.binder'
    _inherit = ['base.binder', 'base.shopware6.connector']
    _apply_on = [
        'shopware6.version',
        'shopware6.product.category',
        'shopware6.res.partner',
        'shopware6.address',
        'shopware6.product.product',
        'shopware6.product.template',
        'shopware6.property.group',
        'shopware6.property.group.option',
        'shopware6.media.folder',
        'shopware6.product.media',
        'shopware6.product.media.file',
        'sales.channel',
        'shopware6.tax',
        'shopware6.account.payment.mode',
        'shopware6.sale.order',
        'shopware6.sale.order.line',
    ]

    _external_field = 'shopware6_id'
    _odoo_field = 'openerp_id'

    def to_openerp(self, external_id, unwrap=False):
        super(Shopware6ModelBinder, self).to_internal(external_id, unwrap=unwrap)
