# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)

class SaleOrderImportMapper(Component):

    _name = 'magento.sale.order.mapper'
    _inherit = 'magento.sale.order.mapper'
    _apply_on = 'magento.sale.order'

    @mapping
    def map_company_id(self, record):
        if self.work.collection.default_company_id:
            return {'company_id': self.work.collection.default_company_id.id}

    @mapping
    def set_order_prepayment(self, record):
        payment_method = record['payment']['method']
        method = self.env['account.payment.mode'].search(
            [('name', '=', payment_method)],
            limit=1,
        )
        if not method:
            method = self.env['account.payment.mode'].with_context(lang='EN').search(
                [('name', '=', payment_method)],
                limit=1,
            )
        if method:
            return {"prepayment":self.work.collection._get_order_prepayment_val(method.id)}