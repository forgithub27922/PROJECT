# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)

class SaleOrderLineImportMapper(Component):

    _inherit = 'shopware.sale.order.line.mapper'

    direct = [('quantity', 'product_uom_qty'),
              ('articleNumber', 'name'),
              ('id', 'shopware_id')
              ]

    def read_price_unit(self, record, product_data):
        unit_price = False
        if product_data:
            main_detail = product_data.get("mainDetail")
            for price in main_detail.get("prices"):
                if int(price.get("from")) <= int(record.get("quantity")) and int(price.get("to") if price.get("to") != 'beliebig' else 9999) >= int(record.get("quantity")):
                    unit_price = price.get("price")
        return unit_price

    @mapping
    def unit_price(self, record):
        binder = self.binder_for('shopware.product.template')
        product_read = self.component(usage='record.exporter', model_name='shopware.product.template')
        if int(record.get("articleId")) <= 0:
            if record.get("articleNumber"):
                product_data = product_read.backend_adapter.read(record['articleNumber']+str("?useNumberAsId=true"))
                unit_price = self.read_price_unit(record, product_data)
                return {'price_unit': unit_price} if unit_price else {'price_unit': record.get("price")}
            else:
                return {'price_unit': record.get("price")}
        product_data = product_read.backend_adapter.read(record['articleId'])
        unit_price = self.read_price_unit(record, product_data)
        return {'price_unit': unit_price} if unit_price else {'price_unit': record.get("price")}

class SaleOrderImportMapper(Component):

    _inherit = 'shopware.sale.order.mapper'
    _apply_on = 'shopware.sale.order'

    def _add_shipping_line(self, map_record, values):

        record = map_record.source
        if record.get("dispatchId", False):
            delivery_carrier = self.env["delivery.carrier"].sudo().search([('shopware_id', '=', record.get("dispatchId", False))], limit=1)
            if delivery_carrier:
                values["carrier_id"] = delivery_carrier.id
                #line = (0, 0, {"product_id": delivery_carrier.product_id.id})
                #values['order_line'].append(line)
                return values
        return values

    @mapping
    def map_prepayment_flag(self, record):
        if int(record.get("paymentId","0")) == 5:
            return {"prepayment": True}
        return {"prepayment": False}

    @mapping
    def map_sales_channel_analytic_account(self, record):
        return {"team_id": 11, 'analytic_account_id':45}

    @mapping
    def set_price_list(self, record):
        if getattr(self,"backend_record", False):
            return {"pricelist_id": self.backend_record.company_id.pricelist_id.id}
        return {}

class SaleOrderImporter(Component):
    _inherit = 'shopware.sale.order.importer'
    _apply_on = 'shopware.sale.order'

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        #binding.openerp_id.get_delivery_price()
        #binding.openerp_id.set_delivery_line()
        _logger.info("After import hook is called grimm shopware connector ::::::::::::::::::::::::::::::: ==================>>>> %s "% binding)
        return