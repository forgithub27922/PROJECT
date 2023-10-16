# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component


class Shopware6StateExporter(Component):
    _name = 'shopware6.sale.state.exporter'
    _inherit = 'base.exporter'
    _usage = 'shopware6.sale.state.exporter'
    _apply_on = 'shopware6.sale.order'

    ORDER_STATUS_MAPPING = {  # used in connector_shopware_order_comment
        'draft': 'pending',
        'manual': 'processing',
        'progress': 'processing',
        'shipping_except': 'processing',
        'invoice_except': 'processing',
        'done': 'complete',
        'cancel': 'canceled',
        'waiting_date': 'holded'
    }

    def run(self, binding, vals, status, notify=False):
        """ Change the status of the sales order on Shopware6.

        It adds a comment on Shopware6 with a status.
        Sales orders on Shopware6 have a state and a status.
        The state is related to the sale workflow, and the status can be
        modified liberaly.  We change only the status because Shopware6
        handle the state itself.

        When a sales order is modified, if we used the ``sales_order.cancel``
        API method, we would not be able to revert the cancellation.  When
        we send ``cancel`` as a status change with a new comment, we are still
        able to change the status again and to create shipments and invoices
        because the state is still ``new`` or ``processing``.

        :param binding: the binding record of the sales order
        :param allowed_states: list of Odoo states that are allowed
                               for export. If empty, it will export any
                               state.
        :param comment: Comment to display on Shopware6 for the state change
        :param notify: When True, Shopware6 will send an email with the
                       comment
        """
        state = vals.get(status)
        shopware6_id = self.binder.to_external(binding)
        if not shopware6_id:
            return _('Sale is not linked with a Shopware sales order')
        if vals.get("type","") == "order":
            record = self.backend_adapter.change_order_state(shopware6_id, status)
        if vals.get("type","") == "delivery":
            delievry_data = self.backend_adapter.get_delivery(shopware6_id)
            for d_data in delievry_data.get("data", []):
                shopware6_id = d_data.get("id")
                record = self.backend_adapter.change_delivery_state(shopware6_id, status)
        if vals.get("type","") == "invoice":
            transaction_data = self.backend_adapter.get_transactions(shopware6_id)
            if transaction_data:
                shopware6_id = transaction_data.get("data",[{}])[-1].get("id")
                record = self.backend_adapter.change_invoice_state(shopware6_id, status)
        if vals.get("type","") == "ratepay_delivery":
            stock_picking = status
            list_items = []
            for line in stock_picking.move_ids_without_package:
                shopware_line_id = False
                for bind in line.sale_line_id.shopware6_bind_ids:
                    shopware_line_id = bind.shopware6_id
                if shopware_line_id:
                    list_items.append({"id":shopware_line_id,"quantity":line.quantity_done})
            record = self.backend_adapter.change_ratepay_delivery_state(shopware6_id, {"items":list_items,"updateStock":None})




        # if record.get(status) == state:
        #     return _('Shopware sales order is already '
        #              'in state %s') % vals
        # self.backend_adapter.write(shopware6_id, vals)
