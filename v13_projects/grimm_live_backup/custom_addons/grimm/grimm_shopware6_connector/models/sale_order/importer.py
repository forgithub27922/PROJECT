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

# class SaleOrderLineImportMapper(Component):
#
#     _inherit = 'shopware6.sale.order.line.mapper'
#
#     direct = [('quantity', 'product_uom_qty'),
#               ('articleNumber', 'name'),
#               ('id', 'shopware_id')
#               ]
#
#     def read_price_unit(self, record, product_data):
#         unit_price = False
#         if product_data:
#             main_detail = product_data.get("mainDetail")
#             for price in main_detail.get("prices"):
#                 if int(price.get("from")) <= int(record.get("quantity")) and int(price.get("to") if price.get("to") != 'beliebig' else 9999) >= int(record.get("quantity")):
#                     unit_price = price.get("price")
#         return unit_price
#
#     @mapping
#     def unit_price(self, record):
#         binder = self.binder_for('shopware.product.template')
#         product_read = self.component(usage='record.exporter', model_name='shopware.product.template')
#         if int(record.get("articleId")) <= 0:
#             if record.get("articleNumber"):
#                 product_data = product_read.backend_adapter.read(record['articleNumber']+str("?useNumberAsId=true"))
#                 unit_price = self.read_price_unit(record, product_data)
#                 return {'price_unit': unit_price} if unit_price else {'price_unit': record.get("price")}
#             else:
#                 return {'price_unit': record.get("price")}
#         product_data = product_read.backend_adapter.read(record['articleId'])
#         unit_price = self.read_price_unit(record, product_data)
#         return {'price_unit': unit_price} if unit_price else {'price_unit': record.get("price")}

class SaleOrderImportMapper(Component):

    _inherit = 'shopware6.sale.order.mapper'
    _apply_on = 'shopware6.sale.order'

    # def _add_shipping_line(self, map_record, values):
    #     record = map_record.source
    #     if record.get("dispatchId", False):
    #         delivery_carrier = self.env["delivery.carrier"].sudo().search([('shopware6_id', '=', record.get("dispatchId", False))], limit=1)
    #         if delivery_carrier:
    #             values["carrier_id"] = delivery_carrier.id
    #             #line = (0, 0, {"product_id": delivery_carrier.product_id.id})
    #             #values['order_line'].append(line)
    #             return values
    #     return values

    # @mapping
    # def map_prepayment_flag(self, record):
    #     if int(record.get("paymentId","0")) == 5:
    #         return {"prepayment": True}
    #     return {"prepayment": False}

    @mapping
    def map_sales_channel_analytic_account(self, record):
        return {"team_id": 2}

    @mapping
    def map_sales_channel_customer_ref(self, record):
        return_dict = {}
        attr = record.get("data", {}).get("attributes", {})
        channel_id = self.env['sales.channel'].search([('shopware6_id', '=', attr.get("salesChannelId", "XXX"))], limit=1)
        return_dict["customer_comment"] = attr.get("customerComment", "")
        if attr.get("customFields",False):
            return_dict["client_order_ref"] = attr.get("customFields", {}).get("bestellreferenz","")
        if channel_id:
            return_dict["shopware6_channel_id"] = channel_id.id
        return return_dict

    @mapping
    def assign_tax_status(self, record):
        attr = record.get("data",{}).get("attributes",{})
        if attr.get("taxStatus","") == "net":
            return {"shopware6_customer_group_old": 'business'}
        else:
            return {"shopware6_customer_group_old": 'private'}


    # @mapping
    # def set_price_list(self, record):
    #     if getattr(self,"backend_record", False):
    #         return {"pricelist_id": self.backend_record.company_id.pricelist_id.id}
    #     return {}

class SaleOrderImporter(Component):
    _inherit = 'shopware6.sale.order.importer'
    _apply_on = 'shopware6.sale.order'

    def _assign_carrier_id(self, binding):
        shipping_data = self.backend_adapter.get_shipping_method(binding.shopware6_id)
        shipping_method_id = shipping_data.get("data", {})[0].get("attributes", {}).get("shippingMethodId", False)

        shipping_cost = 0
        shipping_cost_tax = shipping_data.get("data", {})[0].get("attributes", {}).get("shippingCosts", {}).get("calculatedTaxes", [])
        tax_status = shipping_data.get("data", {})[0].get("attributes", {}).get("taxStatus","")
        for cost in shipping_cost_tax:
            shipping_cost = cost.get("price")
            if binding.shopware6_customer_group_old == "private":
                shipping_cost = cost.get("price") - cost.get("tax")

        carrier = self.env['delivery.carrier'].sudo().search([('shopware6_id', '=', shipping_method_id)],limit=1,)
        if carrier:
            binding.openerp_id.carrier_id = carrier.id
            delivery_wiz_action = binding.openerp_id.action_open_delivery_wizard()
            delivery_wiz_context = delivery_wiz_action.get("context", {})
            delivery_wiz_context["default_carrier_id"] = carrier.id
            delivery_wiz = (
                self.env[delivery_wiz_action.get("res_model")]
                    .with_context(**delivery_wiz_context)
                    .create({})
            )
            delivery_wiz._get_shipment_rate()
            delivery_wiz.button_confirm()
            for line in binding.openerp_id.order_line:
                if shipping_cost > 0 and carrier.product_id.id == line.product_id.id:
                    line.price_unit = shipping_cost




    def _after_import(self, binding):
        """ Hook called at the end of the import """
        #binding.openerp_id.get_delivery_price()
        #binding.openerp_id.set_delivery_line()
        record = super(SaleOrderImporter, self)._after_import(binding)
        billing_address = self.backend_adapter.get_billing_address(self.shopware6_id).get("data", [])
        if billing_address:
            company_name = billing_address[0].get("attributes",{}).get("company", False)
            binding.shopware6_customer_group = "business" if company_name else "private"
        self._assign_carrier_id(binding)
        return record