# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Run JOB http://localhost:8213/queue_job/runjob?db=produktion&job_uuid=48709070-887c-4637-bdcf-52531e25a512

import logging
import xmlrpc.client
import base64
import requests

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        for record in self:
            if record.company_id.id == 3:
                record.change_move_location()
        res = super(StockPicking, self).action_done()
        for record in self:
            self._event('on_delivery_confirm').notify(record)
        return res

    def change_move_location(self):
        grimm_warehouse = self.env['stock.warehouse'].sudo().search([('company_id', '=', 1)])
        grimm_picking_type = grimm_warehouse.out_type_id.id #2
        shared_location = grimm_warehouse.lot_stock_id.id #12
        if self.company_id.id == 3 and self.picking_type_id.id == grimm_picking_type:
            for mv in self.move_ids_without_package:
                mv.location_id = shared_location


    def action_assign(self):
        for pick in self:
            if pick.company_id.id == 3:
                pick.change_move_location()
        res = super(StockPicking, self).action_assign()
        return res

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        partenics_picking_type = self.env['stock.warehouse'].sudo().search([('company_id', '=', 3)]).out_type_id.id #18
        grimm_warehouse = self.env['stock.warehouse'].sudo().search([('company_id', '=', 1)])
        grimm_picking_type = grimm_warehouse.out_type_id.id #2
        shared_location = grimm_warehouse.lot_stock_id.id #12
        if res.company_id.id == 3 and res.picking_type_id.id == partenics_picking_type:
            self._cr.execute("UPDATE stock_picking set picking_type_id=%s, location_id=%s where id=%s;" % (grimm_picking_type,shared_location, res.id))
        return res

# class SaleOrderCancelReason(models.Model): # After discussion with Tobias changed to regular model instead of Transient Model
#     _inherit = 'sale.order.cancel.reason'
#     _description = 'Quotation Reject Reason'
#
#     name = fields.Selection(
#         [('long_delivery', 'Too long delivery time'),
#          ('expensive', 'We were priced too expensive'),
#          ('changed_by_customer', 'Customer has made changes/exchange'),
#          ('wrong_product', 'Wrong product ordered / does not fit'),
#          ('not_paid', 'Customer has not paid in advance'),
#          ('wrong_address', 'Billing/delivery address was not correct'),
#          ('wrong_delivery', 'Wrong Delivery'),
#          ('other', 'Other Reason')],
#         string='Select Reason', required=True)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopware6_price_unit = fields.Float(string='Shopware6 Price Unit')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line. This is inherited for rounding issue.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # GRIMM START
            for binding in line.order_id.shopware6_bind_ids:
                if line.shopware6_price_unit > 0 and round(abs(line.price_unit-line.shopware6_price_unit),5) > 0 and round(abs(line.price_unit-line.shopware6_price_unit),5) < 0.05:
                    price = line.shopware6_price_unit * (1 - (line.discount or 0.0) / 100.0)
            # GRIMM END

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ecommerce_link = fields.Html(string='E-Commerce link', compute="_get_ecommerce_link")
    shopware6_channel_id = fields.Many2one("sales.channel", string="Sales Channel")
    order_confirm_date = fields.Datetime("Confirmation date")
    shopware6_customer_group = fields.Selection(string='Customer Group',selection=[('business', 'Business Customer'), ('private', 'Private Customer')])
    shopware6_customer_group_old = fields.Selection(string='Customer Group Old', selection=[('business', 'Business Customer'),
                                                                                    ('private', 'Private Customer')])
    compute_amount_due = fields.Float(string='Amount Due', compute="_get_amount_due")

    def _replace_place_holder(self, soup, tag="span", tag_id="field_"):
        for sp in soup.find_all(tag, recursive=True):
            try:
                id_name = sp.attrs.get("id", "")
                if id_name.startswith(tag_id):
                    field_name = id_name.split(tag_id, 1)[-1]
                    fields = field_name.split(".")
                    final_val = self
                    for f in fields:
                        final_val = getattr(final_val, f, False)
                    if final_val:
                        if isinstance(final_val, datetime) or isinstance(final_val, date):
                            final_val = str(final_val.strftime("%d.%m.%Y"))  # Changed date format to DD.MM.YYYY
                        if tag == "a":
                            if sp.get("href", False) and "mailto:" in sp.get("href", ""):
                                sp["href"] = "mailto:%s"%final_val
                        else:
                            sp.string = str(final_val)
            except Exception as e:
                _logger.info("========ERROR in beautiful soap ===> %s" % str(e))
                pass

    @api.onchange("order_subject", "validity_date","user_id")
    def _onchange_order_subject(self):
        if self.salutation_text_offer:
            soup = BeautifulSoup(self.salutation_text_offer,features="lxml")
            self._replace_place_holder(soup, tag="span",tag_id="field_")
            self._replace_place_holder(soup, tag="a", tag_id="link_")
            self.salutation_text_offer = soup

    def _get_amount_due(self):
        self.compute_amount_due = 0
        for this in self:
            if this.state not in ['draft', 'cancel']:
                this.compute_amount_due = sum(this.invoice_ids.filtered(lambda r: r.state in ('posted', 'proforma2')).mapped('amount_residual'))

    def _track_subtype(self, init_values):
        self.ensure_one()
        res = super(SaleOrder, self)._track_subtype(init_values)
        if 'state' in init_values and self.state == 'sale':
            self.order_confirm_date = fields.Datetime.now()
        return res

    def _create_delivery_line(self, carrier, price_unit):
        sol = super(SaleOrder, self)._create_delivery_line(carrier, price_unit)
        carrier_with_partner_lang = carrier.with_context(lang=sol.order_id.partner_id.lang)
        if carrier_with_partner_lang.product_id.description_sale:
            so_description = '%s' % (carrier_with_partner_lang.product_id.description_sale)
            sol.name = so_description
        else:
            sol.name = ""
        if self.team_id.id == 2: # Team need default drop shipping option for shop order.
            sol.route_id = 6
        return sol

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for record in self:
            self._event('on_order_confirm').notify(record)
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for record in self:
            self._event('on_order_cancel').notify(record)
        return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        for record in self:
            self._event('on_order_draft').notify(record)
        return res

    def _get_ecommerce_link(self):
        self.ecommerce_link = '#'
        for this in self:
            back_link = "#"
            for binding in this.shopware6_bind_ids:
                if binding.shopware6_id:
                    back_link = "%sadmin#/sw/order/detail/%s/base" % (binding.backend_id.location, binding.shopware6_id)
            this.ecommerce_link = "<a target='new' href='%s' class='link-success'>Back End</a>" % (back_link)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    shopware6_id = fields.Char("Shopware6 ID")

class SaleOrderAdapter(Component):
    _name = 'shopware6.sale.order.adapter'
    _inherit = 'shopware6.sale.order.adapter'
    _apply_on = 'shopware6.sale.order'

    _shopware_uri = 'api/v3/order/'

    def get_shipping_method(self, id):
        return self._call('get', '%s%s/deliveries' % (self._shopware_uri, id), [{}])

    def get_billing_address(self, id):
        return self._call('get', '%s%s/billing-address' % (self._shopware_uri, id), [{}])

class Shopware6StockPickingListener(Component):
    _name = 'shopware6.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def export_webhook_message(self, record):
        record =  {
                "Name": "Ratepay Status send",
                "Order Number": record.sale_id.name,
                "URL": record.sale_id.ecommerce_link,
                "Exported By": "<a href='mailto:%s'>%s</a>" % (self.env.user.login, self.env.user.partner_id.name)
            }
        for backend in self.env['shopware6.backend'].search([]):
            team_url = backend.ratepay_team_webhook_url
            if record and team_url:
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
                    _logger.info("Message posted to microsoft team successfully...")

    def on_delivery_confirm(self, record):
        for binding in record.sale_id.shopware6_bind_ids:
            final_state = 'open'
            all_state = list(set(binding.picking_ids.mapped("state")))
            if 'cancel' in all_state:
                all_state.remove('cancel')
            if all_state:
                if len(all_state) == all_state.count('done'):
                    final_state = "ship"
                else:
                    final_state = "ship_partially"
            if final_state == "ship":
                if 'posted' in list(set(binding.invoice_ids.mapped("state"))):
                    binding.with_delay(priority=6, description="Change Sale order %s state to done."%record.sale_id.name).export_state_change({'type': 'order'}, 'complete')
            binding.with_delay(priority=6, description="Change Sale order %s delivery state to %s."%(record.sale_id.name,final_state)).export_state_change({'type': 'delivery'}, final_state)

        if record.sale_id and record.sale_id.payment_mode_id and (record.sale_id.payment_mode_id.id == 21 or 'ratepay' in record.sale_id.payment_mode_id.name):
            for binding in record.sale_id.shopware6_bind_ids:
                try:
                    binding.with_delay(priority=6,description="Ratepay delivery confirmation for %s"%record.sale_id.name).export_state_change({'type': 'ratepay_delivery'}, record)
                    self.export_webhook_message(record)
                except:
                    pass

class SaleReport(models.Model):
    '''
    Added to display SKU in sales report.
    '''
    _inherit = "sale.report"

    product_sku = fields.Char('SKU', related='product_id.default_code', store=True)
    product_shopware_active = fields.Boolean('Shopware Aktive', related='product_id.shopware_active', store=True)
    product_ecom_categ_id = fields.Many2one('product.category',string='E-commerce Category', related='product_id.ecom_categ_id', store=True)
    product_full_details = fields.Char('Product Full Details', related='product_id.full_details', store=True)
    product_shopware6_shopping_prio_id = fields.Many2one('shopware6.shopping.prio', string='Shopping Prio', related='product_id.shopware6_shopping_prio_id', store=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_sku'] = ', p.default_code as product_sku'
        groupby += ', p.default_code'
        fields['product_shopware_active'] = ', p.shopware_active as product_shopware_active'
        groupby += ', p.shopware_active'
        fields['product_ecom_categ_id'] = ', p.ecom_categ_id as product_ecom_categ_id'
        groupby += ', p.ecom_categ_id'
        fields['product_full_details'] = ', p.full_details as product_full_details'
        groupby += ', p.full_details'
        fields['product_shopware6_shopping_prio_id'] = ', p.shopware6_shopping_prio_id as product_shopware6_shopping_prio_id'
        groupby += ', p.shopware6_shopping_prio_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

class Shopware6InvoiceListener(Component):
    _name = 'shopware6.account.invoice.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['account.move']

    def on_invoice_validated(self, record):
        if record.sale_order_id and record.sale_order_id.shopware6_bind_ids:
            shopware6_id = False
            for bind in record.sale_order_id.shopware6_bind_ids:
                shopware6_id = bind.shopware6_id
            if shopware6_id:
                document_vals = {}
                document_vals["name"] = "Invoice Document"
                document_vals["doc_number"] = record.name
                document_vals["doc_comment"] = record.name
                document_vals["doc_datetime"] = datetime.now()
                document_vals["doc_type"] = "invoice"
                document_vals["order_id"] = shopware6_id
                report_id = self.env['ir.actions.report'].search([('report_name', '=',
                                                                   self.env['ir.config_parameter'].get_param(
                                                                       'datev_export.invoice_report', default=False))])
                if len(report_id) > 1:
                    report_id = report_id[0]
                (result, format) = report_id.render_qweb_pdf([record.id])
                document_vals["document"] = base64.encodestring(result)
                backends = self.env['shopware6.backend'].search([])
                for backend in backends:
                    document_vals["backend_id"] = backend.id
                    document_id = self.env["shopware6.document"].create(document_vals)

class Shopware6SaleOrderListener(Component):
    _name = 'shopware6.sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_order_confirm(self, record):
        #GRIMM START for sending safety email...
        if record.state == 'sale':
            all_product_ids = record.order_line.mapped("product_id.id")
            all_product_ids.append(0)
            record._cr.execute("select distinct(%s) from media_manager_product_product_rel where product_id in %s and media_id in (select id from media_manager where active='t' and send_email='t' and document_type=5);" % ("media_id",tuple(all_product_ids)))
            media_ids = [x[0] for x in record._cr.fetchall()]
            media_manager_ids = record.env["media.manager"].sudo().browse(media_ids)
            template = self.env.ref('grimm_shopware6_connector.email_template_send_email_with_sicherheitsdatenblatt',raise_if_not_found=False)
            template.attachment_ids = [(6,0,[])]  # Removed previous attachment to email template.
            attach_ids = []
            for attach in media_manager_ids.filtered(lambda r: r.data):
                attachment = {
                    'name': str(attach.filename or attach.name),
                    'datas': attach.data,
                    'datas_fname': str(attach.name),
                    'type': 'binary'
                }
                ir_id = self.env['ir.attachment'].sudo().create(attachment)
                attach_ids.append(ir_id.id)
            if attach_ids:
                template.attachment_ids = [(6, 0, attach_ids)]  # Added attachment to email template.
                template.sudo().send_mail(record.id, raise_exception=False, force_send=True,notif_layout="mail.message_notification_email")
        # GRIMM END for sending safety email...

        # Marking related opportunity as won after confirming an offer.
        if record.opportunity_id:
            record.opportunity_id.action_set_won()


        for binding in record.shopware6_bind_ids:
            binding.with_delay(priority=6, description="Change Sale order %s state to process."%record.name).export_state_change({'type': 'order'},'process')  # After confirm always change state to shopware in process
            if record.state != 'prepayment':
                #binding.with_delay().export_state_change({'type': 'delivery'}, 'ship')
                if record.prepayment:
                    binding.with_delay(priority=6, description="Change Sale order %s Invoice state to paid."%record.name).export_state_change({'type': 'invoice'}, 'paid')

    def on_order_cancel(self, record):
        if record.opportunity_id: # On cancelling an offer mark opportunity as lost.
            record.opportunity_id.action_set_lost()
        for binding in record.shopware6_bind_ids:
            binding.with_delay(priority=6, description="Change Sale order %s state to cancel."%record.name).export_state_change({'type': 'order'}, 'cancel')
            binding.with_delay(priority=6, description="Change Sale order %s Delivery state to cancel."%record.name).export_state_change({'type': 'delivery'}, 'cancel')
            if record.prepayment:
                binding.with_delay(priority=6, description="Change Sale order %s Invoice state to cancel."%record.name).export_state_change({'type': 'invoice'}, 'cancel')

    def on_order_draft(self, record):
        for binding in record.shopware6_bind_ids:
            binding.with_delay(priority=6, description="Change Sale order %s state to reopen."%record.name).export_state_change({'type': 'order'}, 'reopen')
            binding.with_delay(priority=6, description="Change Sale order %s Delivery state to reopen."%record.name).export_state_change({'type': 'delivery'}, 'reopen')
            if record.prepayment:
                binding.with_delay(priority=6, description="Change Sale order %s Invoice state to reopen."%record.name).export_state_change({'type': 'invoice'}, 'reopen')