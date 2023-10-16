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


class Shopware6SaleOrder(models.Model):
    _name = 'shopware6.sale.order'
    _inherit = 'shopware6.binding'
    _description = 'Shopware6 Sale Order'
    _inherits = {'sale.order': 'openerp_id'}

    openerp_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    state = fields.Selection(related="openerp_id.state")
    shopware6_order_line_ids = fields.One2many(
        comodel_name='shopware6.sale.order.line',
        inverse_name='shopware6_order_id',
        string='Shopware6 Order Lines'
    )
    total_amount = fields.Float(
        string='Total amount',
        digits='Account'
    )
    total_amount_tax = fields.Float(
        string='Total amount w. tax',
        digits='Account'
    )
    shopware6_order_id = fields.Integer(string='Shopware6 Order ID',
                                      help="'order_id' field in Shopware")
    # when a sale order is modified, Shopware creates a new one, cancels
    # the parent order and link the new one to the canceled parent
    shopware6_parent_id = fields.Many2one(comodel_name='shopware6.sale.order',
                                        string='Parent Shopware Order')
    # storeview_id = fields.Many2one(comodel_name='shopware.storeview', string='Shopware Storeview')
    # shopware_store_id = fields.Many2one(related='storeview_id.store_id', string='Storeview', readonly=True)

    @job(default_channel='root.shopware6')
    def export_state_change(self, vals, status, notify=None):
        """ Change state of a sales order on Shopware6 """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='shopware6.sale.state.exporter')
            return exporter.run(self, vals, status)

    @job(default_channel='root.shopware6')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from Shopware """
        #assert 'shopId' in filters, ('Missing information about Shopware Storeview')
        _super = super(Shopware6SaleOrder, self)
        return _super.import_batch(backend, filters=filters)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.sale.order',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    is_shopware6_amount_diff = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_amount_diff')

    def _get_is_shopware6_amount_diff(self):
        for this in self:
            if this.shopware6_amount_total > 0 and abs(this.shopware6_amount_total - this.amount_total) > 0.50:
                this.is_shopware6_amount_diff = True
            else:
                this.is_shopware6_amount_diff = False

    shopware6_amount_total = fields.Float("Shopware6 Amount Total", compute_sudo=True, digits=(12, 6), readonly=True,
                                 help='Total order amount from Shopware6')

    @api.depends('shopware6_bind_ids', 'shopware6_bind_ids.shopware6_parent_id')
    def get_parent_id(self):
        """ Return the parent order.

        For Shopware sales orders, the shopware parent order is stored
        in the binding, get it from there.
        """
        super(SaleOrder, self).get_parent_id()
        for order in self:
            if not order.shopware6_bind_ids:
                continue
            # assume we only have 1 SO in Odoo for 1 SO in Shopware
            assert len(order.shopware6_bind_ids) == 1
            shopware_order = order.shopware6_bind_ids[0]
            if shopware_order.shopware6_parent_id:
                self.parent_id = shopware_order.shopware_parent_id.openerp_id

    def _shopware_state_change(self, vals, status):
        """ Cancel sales order on Shopware

        Do not export the other state changes, Shopware handles them itself
        when it receives shipments and invoices.
        """
        for order in self:
            for binding in order.shopware6_bind_ids:
                job_descr = _("Changing sales order %s state to  %s") % (binding.shopware6_id, vals)
                binding.with_delay(
                    description=job_descr
                ).export_state_change(vals, status)

    def update_order_state_shopware(self, days=30):
        domain = [('openerp_id.state', 'in', ['done','deliverynotice', 'sale']), ('openerp_id.date_order', '>=', str(datetime.now() - timedelta(days=days)))]
        sale_orders = self.env["shopware6.sale.order"].search(domain)
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
        binding_model = self.env['shopware6.sale.order']
        bindings = binding_model.search([('openerp_id', '=', self.id)])
        bindings.write({'openerp_id': new.id})

        for binding in bindings:
            # the sales' status on Shopware is likely 'canceled'
            # so we will export the new status (pending, processing, ...)
            job_descr = _("Reopen sales order %s") % (binding.shopware6_id,)
            binding.with_delay(
                description=job_descr
            ).export_state_change()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self_copy = self.with_context(__copy_from_quotation=True)
        new = super(SaleOrder, self_copy).copy(default=default)
        self_copy._shopware_link_binding_of_copy(new)
        return new


class Shopware6SaleOrderLine(models.Model):
    _name = 'shopware6.sale.order.line'
    _inherit = 'shopware6.binding'
    _description = 'Shopware6 Sale Order Line'
    _inherits = {'sale.order.line': 'openerp_id'}

    shopware6_order_id = fields.Many2one(comodel_name='shopware6.sale.order',
                                       string='Shopware6 Sale Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    openerp_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')

    backend_id = fields.Many2one(
        related='shopware6_order_id.backend_id',
        string='Shopware6 Backend',
        readonly=True,
        store=True,
        # override 'shopware6.binding', can't be INSERTed if True:
        required=False,
    )
    tax_rate = fields.Float(string='Tax Rate',
                            digits='Account')
    notes = fields.Char()



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.sale.order.line',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
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
            binding_model = self.env['shopware6.sale.order.line']
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
    _name = 'shopware6.sale.order.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.sale.order'

    _shopware_uri = 'api/v3/order/'

    def json_to_qs(self, object, prefix="", string="", first=False):
        for k, v in object.items():
            if type(v) == type([]):
                for index, val in enumerate(v):
                    temp = "%s%s[%s]" % (prefix, k, index if type(val) == type({}) else "")
                    if type(val) not in [type([]), type({})]:
                        string += "%s[%s][%s]=%s&" % (prefix, k, index, val)
                    else:
                        string = self.json_to_qs(val, temp, string)
            elif type(v) == type({}):
                temp = "%s%s"%(prefix,k) if first else "%s[%s]"%(prefix,k)
                string += self.json_to_qs(v, temp, "")
            else:
                string += "%s[%s]=%s&" % (prefix, k, v)

        return string

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids
        {
            "filter":[
                {
                    "type":"equals",
                    "field":"id",
                    "value":"7395906d1d9d46e5b0109fddd2c7c11b"
                }
            ]
        }
        here type could be equals, contains,
        filter[0][type]=equals&filter[0][field]=id&filter[0][value]=7395906d1d9d46e5b0109fddd2c7c11b
        :rtype: list
        """
        if filters:
            query_string = self.json_to_qs(filters,"","", True)

        result = self._call('get','%s?%s' % (self._shopware_uri,query_string),{})
        return result.get('data', result)


    def read(self, id, attributes=None):
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

    def get_customer(self, id):
        return self._call('get', 'api/v3/customer/%s' % (id), [{}])

    def order_address(self, id):
        #return self._call('get', '%s%s/addresses?includes[order_address][]=id' % (self._shopware_uri, id), [{}])
        return self._call('get', '%s%s/addresses' % (self._shopware_uri, id), [{}])

    def get_order_lines(self, id):
        return self._call('get', '%s%s/line-items' % (self._shopware_uri, id), [{}])

    def change_order_state(self, id, status):
        return self._call('POST', 'api/v2/_action/order/%s/state/%s' % (id, status), [{}])

    def change_invoice_state(self, id, status):
        return self._call('POST', 'api/v2/_action/order_transaction/%s/state/%s' % (id, status), [{}])

    def change_delivery_state(self, id, status):
        return self._call('POST', 'api/v2/_action/order_delivery/%s/state/%s' % (id, status), [{}])
    def change_ratepay_delivery_state(self, id, payload):
        return self._call('POST', 'api/v2/ratepay/order-management/deliver/%s' % (id), payload)

    def get_transactions(self, id):
        return self._call('get', '%s%s/transactions' % (self._shopware_uri, id), [{}])

    def get_machine_state(self, id):
        return self._call('get', 'api/v3/state-machine-state/%s' % (id), [{}])

    def get_delivery(self, id):
        return self._call('get', '%s%s/deliveries' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update records on the external system """
        return self._call('PATCH', self._shopware_uri+str(id), data)