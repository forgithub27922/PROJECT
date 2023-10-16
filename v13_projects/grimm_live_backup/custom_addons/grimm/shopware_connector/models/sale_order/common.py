# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from datetime import datetime, timedelta

from ...components.backend_adapter import SHOPWARE_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class ShopwareSaleOrder(models.Model):
    _name = 'shopware.sale.order'
    _inherit = 'shopware.binding'
    _description = 'Shopware Sale Order'
    _inherits = {'sale.order': 'openerp_id'}

    openerp_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    shopware_order_line_ids = fields.One2many(
        comodel_name='shopware.sale.order.line',
        inverse_name='shopware_order_id',
        string='Shopware Order Lines'
    )
    total_amount = fields.Float(
        string='Total amount',
        digits='Account'
    )
    total_amount_tax = fields.Float(
        string='Total amount w. tax',
        digits='Account'
    )
    shopware_order_id = fields.Integer(string='Shopware Order ID',
                                      help="'order_id' field in Shopware")
    # when a sale order is modified, Shopware creates a new one, cancels
    # the parent order and link the new one to the canceled parent
    shopware_parent_id = fields.Many2one(comodel_name='shopware.sale.order',
                                        string='Parent Shopware Order')
    #storeview_id = fields.Many2one(comodel_name='shopware.storeview', string='Shopware Storeview')
    #shopware_store_id = fields.Many2one(related='storeview_id.store_id', string='Storeview', readonly=True)

    @job(default_channel='root.shopware')
    def export_state_change(self, vals, status, notify=None):
        """ Change state of a sales order on Shopware """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='shopware.sale.state.exporter')
            return exporter.run(self, vals, status)

    @job(default_channel='root.shopware')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from Shopware """
        #assert 'shopId' in filters, ('Missing information about Shopware Storeview')
        _super = super(ShopwareSaleOrder, self)
        return _super.import_batch(backend, filters=filters)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopware_bind_ids = fields.One2many(
        comodel_name='shopware.sale.order',
        inverse_name='openerp_id',
        string="Shopware Bindings",
    )

    @api.depends('shopware_bind_ids', 'shopware_bind_ids.shopware_parent_id')
    def get_parent_id(self):
        """ Return the parent order.

        For Shopware sales orders, the shopware parent order is stored
        in the binding, get it from there.
        """
        super(SaleOrder, self).get_parent_id()
        for order in self:
            if not order.shopware_bind_ids:
                continue
            # assume we only have 1 SO in Odoo for 1 SO in Shopware
            assert len(order.shopware_bind_ids) == 1
            shopware_order = order.shopware_bind_ids[0]
            if shopware_order.shopware_parent_id:
                self.parent_id = shopware_order.shopware_parent_id.openerp_id

    def _shopware_state_change(self, vals, status):
        """ Cancel sales order on Shopware

        Do not export the other state changes, Shopware handles them itself
        when it receives shipments and invoices.
        """
        for order in self:
            for binding in order.shopware_bind_ids:
                job_descr = _("Changing sales order %s state to  %s") % (binding.shopware_id, vals)
                binding.with_delay(
                    description=job_descr
                ).export_state_change(vals, status)

    def update_order_state_shopware(self, days=30):
        domain = [('openerp_id.state', 'in', ['done','deliverynotice', 'sale']), ('openerp_id.date_order', '>=', str(datetime.now() - timedelta(days=days)))]
        sale_orders = self.env["shopware.sale.order"].search(domain)
        for order in sale_orders:
            for inv in order.openerp_id.invoice_ids:
                if inv.state == 'paid':
                    order.openerp_id._shopware_state_change({'paymentStatusId':2}, status = 'paymentStatusId') #If invoice is paid need to send status to shopware
                else:
                    order.openerp_id._shopware_state_change({'paymentStatusId': 10}, status = 'paymentStatusId')
            is_pick_done = False
            for picking in order.openerp_id.picking_ids:
                if picking.state == 'done':
                    is_pick_done = True
                else:
                    is_pick_done = False
                    break
            if is_pick_done:
                order.openerp_id._shopware_state_change({'orderStatusId': 7}, status = 'orderStatusId')#If all picking is in done state need to send order status on shopware.

    def _shopware_link_binding_of_copy(self, new):
        # link binding of the canceled order to the new order, so the
        # operations done on the new order will be sync'ed with Shopware
        if self.state != 'cancel':
            return
        binding_model = self.env['shopware.sale.order']
        bindings = binding_model.search([('openerp_id', '=', self.id)])
        bindings.write({'openerp_id': new.id})

        for binding in bindings:
            # the sales' status on Shopware is likely 'canceled'
            # so we will export the new status (pending, processing, ...)
            job_descr = _("Reopen sales order %s") % (binding.shopware_id,)
            binding.with_delay(
                description=job_descr
            ).export_state_change()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self_copy = self.with_context(__copy_from_quotation=True)
        new = super(SaleOrder, self_copy).copy(default=default)
        self_copy._shopware_link_binding_of_copy(new)
        return new


class ShopwareSaleOrderLine(models.Model):
    _name = 'shopware.sale.order.line'
    _inherit = 'shopware.binding'
    _description = 'Shopware Sale Order Line'
    _inherits = {'sale.order.line': 'openerp_id'}

    shopware_order_id = fields.Many2one(comodel_name='shopware.sale.order',
                                       string='Shopware Sale Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    openerp_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')
    backend_id = fields.Many2one(
        related='shopware_order_id.backend_id',
        string='Shopware Backend',
        readonly=True,
        store=True,
        # override 'shopware.binding', can't be INSERTed if True:
        required=False,
    )
    tax_rate = fields.Float(string='Tax Rate',
                            digits='Account')
    notes = fields.Char()

    @api.model
    def create(self, vals):
        shopware_order_id = vals['shopware_order_id']
        binding = self.env['shopware.sale.order'].browse(shopware_order_id)
        vals['order_id'] = binding.openerp_id.id
        binding = super(ShopwareSaleOrderLine, self).create(vals)
        # FIXME triggers function field
        # The amounts (amount_total, ...) computed fields on 'sale.order' are
        # not triggered when shopware.sale.order.line are created.
        # It might be a v8 regression, because they were triggered in
        # v7. Before getting a better correction, force the computation
        # by writing again on the line.
        # line = binding.openerp_id
        # line.write({'price_unit': line.price_unit})
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopware_bind_ids = fields.One2many(
        comodel_name='shopware.sale.order.line',
        inverse_name='openerp_id',
        string="Shopware Bindings",
    )

    @api.model
    def create(self, vals):
        old_line_id = None
        if self.env.context.get('__copy_from_quotation'):
            # when we are copying a sale.order from a canceled one,
            # the id of the copied line is inserted in the vals
            # in `copy_data`.
            old_line_id = vals.pop('__copy_from_line_id', None)
        new_line = super(SaleOrderLine, self).create(vals)
        if old_line_id:
            # link binding of the canceled order lines to the new order
            # lines, happens when we are using the 'New Copy of
            # Quotation' button on a canceled sales order
            binding_model = self.env['shopware.sale.order.line']
            bindings = binding_model.search([('openerp_id', '=', old_line_id)])
            if bindings:
                bindings.write({'openerp_id': new_line.id})
        return new_line

    @api.returns('self', lambda value: value.id)
    def copy_data(self, default=None):
        data = super(SaleOrderLine, self).copy_data(default=default)[0]
        if self.env.context.get('__copy_from_quotation'):
            # copy_data is called by `copy` of the sale.order which
            # builds a dict for the full new sale order, so we lose the
            # association between the old and the new line.
            # Keep a trace of the old id in the vals that will be passed
            # to `create`, from there, we'll be able to update the
            # Shopware bindings, modifying the relation from the old to
            # the new line.
            data['__copy_from_line_id'] = self.id
        return [data]


class SaleOrderAdapter(Component):
    _name = 'shopware.sale.order.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.sale.order'

    _shopware_uri = 'orders/'
    _shopware_path = '{model}/view/order_id/{id}'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if filters:
            query_string = ""
            index = 0
            for filt in filters:
                query_string += "filter[%s][property]=%s&filter[%s][expression]=%s&filter[%s][value]=%s&"%(index,filt.get("property"),index,filt.get("expression","="),index,filt.get("value"))
                index += 1
            self._shopware_uri = "orders?%s"%query_string
        return self._call('get','%s' % self._shopware_uri,{})

    def read(self, id, attributes=None):
        return self._call('get', '%s%s?useNumberAsId=true' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update records on the external system """
        return self._call('put', self._shopware_uri+str(id)+str("?useNumberAsId=true"), data)