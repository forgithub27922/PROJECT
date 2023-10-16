# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component


class ShopwareStateExporter(Component):
    _name = 'shopware.sale.state.exporter'
    _inherit = 'base.exporter'
    _usage = 'shopware.sale.state.exporter'
    _apply_on = 'shopware.sale.order'

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
        """ Change the status of the sales order on Shopware.

        It adds a comment on Shopware with a status.
        Sales orders on Shopware have a state and a status.
        The state is related to the sale workflow, and the status can be
        modified liberaly.  We change only the status because Shopware
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
        :param comment: Comment to display on Shopware for the state change
        :param notify: When True, Shopware will send an email with the
                       comment
        """
        state = vals.get(status)
        shopware_id = self.binder.to_external(binding)
        if not shopware_id:
            return _('Sale is not linked with a Shopware sales order')
        record = self.backend_adapter.read(shopware_id)
        if record.get(status) == state:
            return _('Shopware sales order is already '
                     'in state %s') % vals
        self.backend_adapter.write(shopware_id, vals)
