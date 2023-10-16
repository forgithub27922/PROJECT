# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import xmlrpc.client
import requests
from odoo import api, models, fields
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.connector.exception import IDMissingInBackend

_logger = logging.getLogger(__name__)

class MagentoInvoiceExporter(Component):
    """ Export invoices to Magento """
    _name = 'magento.account.invoice.exporter'
    _inherit = 'magento.account.invoice.exporter'
    _apply_on = ['magento.account.invoice']

    def _after_export(self, magento_id=False):
        '''
        This method will again execute after exporting Invoice to Magento for capture invoice.
        :return:
        '''
        if magento_id:
            magento_invoice = magento_id
            magento_id = self._backend_adapter.capture(int(magento_invoice))

    def run(self, binding):
        """ Run the job to export the validated/paid invoice """

        magento_order = binding.magento_order_id
        magento_store = magento_order.store_id
        mail_notification = magento_store.send_invoice_paid_mail

        lines_info = self._get_lines_info(binding)
        magento_id = None
        try:
            magento_id = self._export_invoice(magento_order.magento_id,
                                               lines_info,
                                               mail_notification)
        except xmlrpc.client.Fault as err:
            # When the invoice is already created on Magento, it returns:
            # <Fault 102: 'Cannot do invoice for order.'>
            # We'll search the Magento invoice ID to store it in Odoo
            if err.faultCode == 102:
                _logger.debug('Invoice already exists on Magento for '
                              'sale order with magento id %s, trying to find '
                              'the invoice id.',
                              magento_order.magento_id)
                magento_id = self._get_existing_invoice(magento_order)
                if magento_id is None:
                    # In that case, we let the exception bubble up so
                    # the user is informed of the 102 error.
                    # We couldn't find the invoice supposedly existing
                    # so an investigation may be necessary.
                    raise
            else:
                raise
        # When the invoice already exists on Magento, it may return
        # a 102 error (handled above) or return silently without ID
        if not magento_id:
            # If Magento returned no ID, try to find the Magento
            # invoice, but if we don't find it, let consider the job
            # as done, because Magento did not raised an error
            magento_id = self._get_existing_invoice(magento_order)

        if magento_id:
            self.binder.bind(magento_id, binding.id)
        self._after_export(magento_id)


class AccountInvoiceAdapter(Component):
    """ Backend Adapter for the Magento Invoice """

    _name = 'magento.invoice.adapter'
    _inherit = 'magento.invoice.adapter'
    _apply_on = 'magento.account.invoice'

    _magento_model = 'sales_order_invoice'
    _admin_path = 'sales_invoice/view/invoice_id/{id}'

    def capture(self, order_increment_id):
        """ Create a record on the external system """
        return self._call('%s.capture' % self._magento_model,
                          [order_increment_id])



class MagentoOrderShipment(models.Model):
    """ Binding Model for the Magento Invoice """
    _name = 'magento.order.shipment'
    _inherit = 'magento.binding'
    _inherits = {'account.move': 'openerp_id'}
    _description = 'Magento Invoice'

    openerp_id = fields.Many2one(comodel_name='account.move',
                              string='Invoice',
                              required=True,
                              ondelete='cascade')
    magento_order_id = fields.Many2one(comodel_name='magento.sale.order',
                                       string='Magento Sale Order',
                                       ondelete='set null')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, openerp_id)',
         'A Magento binding for this Shipping already exists.'),
    ]

    @job(default_channel='root.magento')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self):
        """ Export a validated or paid invoice. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)

class AccountInvoice(models.Model):
    """ Adds the ``one2many`` relation to the Magento bindings
    (``magento_bind_ids``)
    """
    _inherit = 'account.move'

    magento_shipment_ids = fields.One2many(
        comodel_name='magento.order.shipment',
        inverse_name='openerp_id',
        string='Magento Shipment Bindings',
    )


class MagentoOrderShipmentAdapter(Component):
    """ Backend Adapter for the Magento Shipment """

    _name = 'magento.order.shipment.adapter'
    _inherit = 'magento.adapter'
    _apply_on = 'magento.order.shipment'

    _magento_model = 'order_shipment'
    _admin_path = 'sales_invoice/view/invoice_id/{id}'

    def _call(self, method, arguments):
        try:
            return super(MagentoOrderShipmentAdapter, self)._call(method, arguments)
        except xmlrpc.client.Fault as err:
            # this is the error in the Magento API
            # when the invoice does not exist
            if err.faultCode == 100:
                raise IDMissingInBackend
            else:
                raise

    def create(self, order_increment_id, items, comment, email,
               include_comment):
        """ Create a record on the external system """
        return self._call('%s.create' % self._magento_model,
                          [order_increment_id, items, comment,
                           email, include_comment])

    def search_read(self, filters=None, order_id=None):
        """ Search records according to some criterias
        and returns their information

        :param order_id: 'order_id' field of the magento sale order, this
                         is not the same field than 'increment_id'
        """
        if filters is None:
            filters = {}
        if order_id is not None:
            filters['order_id'] = {'eq': order_id}
        return super(MagentoOrderShipmentAdapter, self).search_read(filters=filters)


class MagentoOrderShipmentListener(Component):
    _name = 'magento.order.shipping.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['magento.order.shipment']

    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()


class MagentoInvoiceListener(Component):
    _name = 'magento.account.invoice.listener'
    _inherit = 'magento.account.invoice.listener'
    _apply_on = ['account.move']

    def export_webhook_message_magento(self, order_id):
        record =  {
                "Name": "Magento Order - Ratepay Status send for Magento order",
                "Order Number": order_id.name,
                "Exported By": "<a href='mailto:%s'>%s</a>" % (self.env.user.login, self.env.user.partner_id.name)
            }
        for backend in self.env['shopware6.backend'].search([]):
            team_url = backend.ratepay_team_webhook_url
            if record:
                message_string = "<table class='table'><tbody>"
                for k, v in record.items():
                    message_string += "<tr><td><b>%s</b></td><td>%s</td></tr>" % (k, v)
                message_string += "</tbody></table>"
                data = {
                    "title": "Ratepay delivery confirmation send:",
                    "text": message_string,
                    "themeColor": "00e600",
                    "potentialAction": [
                        {
                            "@context": "http://schema.org",
                            "@type": "ViewAction",
                            "name": "View",
                            "target": [
                                record.get("URL")
                            ]
                        }
                    ]
                }

                r = requests.post(url=team_url, json=data)
                if r.status_code == 200 and r.json() == 1:
                    _logger.info("Message posted to microsoft team successfully for Magento Order...")

    def invoice_create_bindings(self, invoice):
        """
        Create a ``magento.account.invoice` and `magento.order.shipment`` record. This record will then
        be exported to Magento.
        """
        # find the magento store to retrieve the backend
        # we use the shop as many sale orders can be related to an invoice
        sales = invoice.mapped('invoice_line_ids.sale_line_ids.order_id')
        for sale in sales:
            for magento_sale in sale.magento_bind_ids:
                binding_exists = False
                for mag_inv in invoice.magento_bind_ids:
                    if mag_inv.backend_id.id == magento_sale.backend_id.id:
                        binding_exists = True
                        break
                if binding_exists:
                    continue
                # Check if invoice state matches configuration setting
                # for when to export an invoice
                magento_store = magento_sale.store_id
                payment_mode = sale.payment_mode_id
                if payment_mode and payment_mode.create_invoice_on:
                    create_invoice = payment_mode.create_invoice_on
                else:
                    create_invoice = magento_store.create_invoice_on
                if invoice.state == 'posted' and payment_mode.name == 'payone_ratepay':
                    # Team webhook call for old Magento order
                    self.export_webhook_message_magento(sale)


                    #self.env['magento.invoice.buffer'].create({
                    #    'magento_backend_id': magento_sale.backend_id.id,
                    #    'openerp_id': invoice.id,
                    #    'magento_order_id': magento_sale.id})

                    # self.env['magento.account.invoice'].create({
                    #     'backend_id': magento_sale.backend_id.id,
                    #     'openerp_id': invoice.id,
                    #     'magento_order_id': magento_sale.id})

                    # As per suggestion from Marco here I have created magento shipment after creation of Magento Invoice.
                    # Because for RatePay we need Magento Order complete status on Magento side thats why we need shipment of this order.
                    #self.env['magento.shippment.buffer'].create({
                    #    'magento_backend_id': magento_sale.backend_id.id,
                    #    'openerp_id': invoice.id,
                    #    'magento_order_id': magento_sale.id})

                    # self.env['magento.order.shipment'].create({
                    #     'backend_id': magento_sale.backend_id.id,
                    #     'openerp_id': invoice.id,
                    #     'magento_order_id': magento_sale.id})
