# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from .sale import grouplines
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, get_lang
import re
import base64
import urllib.parse

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"

    delivery_address_header = fields.Char('Delivery Address Header')
    print_internal_ref = fields.Boolean(string='Print Internal Reference', help="Prints Art.-Nr. in the report")
    is_invoice_sent = fields.Boolean(string='Grimm Invoice Sent')
    invoice_sent_date = fields.Datetime(string='Invoice sent date')

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_invoice_as_sent'):
            for this in self:
                if this.sale_order_id and this.sale_order_id.team_id and this.sale_order_id.team_id.id == 2:
                    this.with_context(tracking_disable=True).write({'is_invoice_sent': True, 'invoice_sent_date':fields.Datetime.now()})
        return super(AccountInvoice, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def sorted_nicely_list(self, l):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    def is_last_invoice(self):
        self.ensure_one()
        is_last_invoice = False
        if self.sale_order_id and self.sale_order_id.invoice_count > 1:
            print(self.sale_order_id,"Yes this invoice is the last Invoice...")
            down_payment_product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            for inv_line in self.invoice_line_ids:
                if inv_line.product_id.id == int(down_payment_product_id) and inv_line.quantity < 0:
                    is_last_invoice = True
                    break
        return is_last_invoice

    def get_payment_data(self):
        self.ensure_one()
        return self._get_reconciled_info_JSON_values()

    def format_number(self, number):
        self.ensure_one()
        return formatLang(self.env, number, currency_obj=self.currency_id)

    def get_pevious_invices(self):
        self.ensure_one()
        invoices = []
        if self.sale_order_id and self.sale_order_id.invoice_count > 1:
            invoices = self.sale_order_id.invoice_ids.filtered(lambda rec: rec.id != self.id and rec.state not in ['draft','cancel'] and rec.invoice_payment_state in ['paid'])
        return invoices

    def get_amount_untax_taxed_total(self):
        self.ensure_one()
        amount_untaxed = 0.0
        total_tax = 0.0

        for line in self.invoice_line_ids:
            line_tax = 0
            if self.is_last_invoice and line.quantity >= 0:
                amount_untaxed += line.price_subtotal
                for tax in line.tax_ids:
                    line_tax += (float(tax.amount)*float(line.price_subtotal))/100
                total_tax += line_tax
        return [formatLang(self.env, amount_untaxed, currency_obj=self.currency_id), formatLang(self.env, total_tax, currency_obj=self.currency_id),formatLang(self.env, amount_untaxed+total_tax, currency_obj=self.currency_id)]

    def get_sorted_line(self):
        """ Sort the given iterable in the way that humans expect."""
        line_seq_list = []
        final_list = []
        for line in self.invoice_line_ids:
            if line.line_no_stored:
                line_seq_list.append(str(line.line_no_stored+str("***")+str(line.id))) #Added special char to split the id of order line.
            else:
                final_list.append(line)
        line_seq_list = self.sorted_nicely_list(line_seq_list)
        for l in line_seq_list:
            if "***" in l:
                line_id = l.split("***")[1]
                final_list.append(self.env["account.move.line"].browse(int(line_id)))
        return final_list


    def _get_invoice_qrcode(self, invoice=False, border=1, box_size=2):
        invoice = invoice if invoice else self
        import qrcode
        import base64
        from io import BytesIO
        from PIL import Image
        import os

        image_path = str(os.path.dirname(__file__)) + "/grimm_qr.png"
        face = Image.open(image_path)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )

        data = """BCD
001
1
SCT
WELADED1PMB
GRIMM Gastronomiebedarf GmbH
DE44 1605 0000 1000 8709 83
%s

%s
            """ % (invoice.amount_total, invoice.name)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#009FE3", back_color="white")
        pos = ((img.size[0] - face.size[0]) // 2, (img.size[1] - face.size[1]) // 2)
        img.paste(face, pos)

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        return img_str

    def _compute_origin_date(self):
        for invoice in self:
            invoice.origin_date = False
            for sale_order in self.env["sale.order"].search([("name", "=", invoice.invoice_origin)]):
                invoice.origin_date = sale_order.date_order or sale_order.write_date

    def _get_tax_decription(self):
        tax_info = []
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                tax_info.append(tax.description)
        return ', '.join(list(set(tax_info)))


    def _get_discount_information(self):
        for record in self:
            for line in record.invoice_line_ids:
                if line.discount and line.discount > 0:
                    return True
            return False

    def get_payment_date_public(self):
        return self._get_payment_date()

    def get_base64_url_encode_string(self, text=False):
        return urllib.parse.quote(base64.b64encode(text.encode('ascii'))) if text else ""

    def _get_payment_date(self):
        for record in self:
            if record.invoice_date: # As suggestion from Tobias and accounting team added create date
                return (datetime.strptime(str(record.invoice_date), '%Y-%m-%d') + timedelta(days=14)).date().strftime(
                    '%d.%m.%Y')
            elif record.sale_order_id:
                if record.sale_order_id.date_order:
                    return (datetime.strptime(str(record.sale_order_id.date_order), '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=14)).date().strftime('%d.%m.%Y')
                elif record.origin_date:
                    return (datetime.strptime(str(record.origin_date), '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=14)).date().strftime('%d.%m.%Y')
                else:
                    return (datetime.strptime(str(record.create_date), '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=14)).date().strftime('%d.%m.%Y')

    def _get_related_so(self):
        for record in self:
            record.sale_order_id = False
            if record.type in ['out_invoice','out_refund']:
                order_id = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                if order_id:
                    record.sale_order_id = order_id
                else:
                    origin_invoice = self.search([('name', 'like', record.invoice_origin)], limit=1)
                    record.sale_order_id = self.env['sale.order'].search([('name', '=', origin_invoice.invoice_origin)], limit=1)

    def _get_origin_create_date(self):
        for record in self:
            record.origin_create_date = False
            if record.type == 'out_invoice':
                origin = self.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)], limit=1)
                record.origin_create_date = origin.create_date
            if record.type == 'out_refund':
                origin_invoice = self.search([('name', 'like', record.invoice_origin)], limit=1)
                origin = self.env['sale.order'].search(
                    [('name', '=', origin_invoice.invoice_origin)], limit=1)
                record.origin_create_date = origin.create_date

    def _get_da_from_so(self):
        for record in self:
            sale_order_id = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
            record.delivery_address = sale_order_id.partner_shipping_id or False if sale_order_id else False

    def _get_paymentterm(self):
        for record in self:
            record.payment_term_id = record.invoice_payment_term_id
            if record.invoice_payment_term_id:
                record.payment_term_id = record.invoice_payment_term_id
            else:
                if record.invoice_origin:
                    sale_order_id = self.env['sale.order'].search(
                        [('name', '=', record.invoice_origin)], limit=1)
                    if sale_order_id:
                        if sale_order_id.payment_term_id:
                            record.payment_term_id = sale_order_id.payment_term_id
                else:
                    record.payment_term_id = self.env['account.payment.term'].search(
                        [('name', '=', 'Immediate Payment')], limit=1) or 1

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', compute=_get_related_so)

    origin_create_date = fields.Date(string='Sale Order Date',
                                     help="Keep empty to use the invoice date.",
                                     readonly=True, compute=_get_origin_create_date)

    delivery_address = fields.Many2one('res.partner', 'Delivery Address', states={
        'confirmed': [('readonly', True)]}, compute=_get_da_from_so)

    payment_term_id = fields.Many2one('account.payment.term', compute=_get_paymentterm)

    origin_date = fields.Datetime(string="Origin Date", compute="_compute_origin_date")

    def print_invoice_grimm(self):
        return self.env['report'].get_action(self, 'grimm_reports.report_invoice_grimm')

    def wo_invoice_grimm(self):
        if self.id:
            sale_order_id = self.env['sale.order'].search(
                [('name', '=', self.invoice_origin)], limit=1)
            if sale_order_id.state == 'prepayment':
                sale_order_id.action_confirm()

    def send_invoice_grimm(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = None
        comp_id = self.env.user.company_id.id
        try:
            if comp_id == 3:
                template = self.env.ref('grimm_modifications.email_template_edi_invoice_partenics', False)
            else:
                template = self.env.ref('account.email_template_edi_invoice', False)
        except:
            pass
        if not template:
            template = self.env.ref('grimm_reports.email_template_proforma_invoice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            company_id=comp_id,
            #custom_layout="account.mail_template_data_notification_email_account_invoice",
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def sale_layout_lines(self, invoice_id=None):
        """
        Returns invoice lines from a specified invoice ordered by
        sale_layout_category sequence. Used in sale_layout module.

        :Parameters:
            -'invoice_id' (int): specify the concerned invoice.
        """
        ordered_lines = self.browse(invoice_id).invoice_line_ids
        # We chose to group first by category model and, if not present, by invoice name
        sortkey = lambda x: x.layout_category_id if x.layout_category_id else ''

        return grouplines(self, ordered_lines, sortkey)

    def _get_delivery_date(self, product_id):
        cal_date = ''
        _logger.info('Report Type ' + str(self.type))
        if self.type == 'out_invoice':
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
            # _logger.info('DELIVERY DATE ' + str(sale_order) + product_id)
            purchase_order = self.env['purchase.order'].search([('origin', '=', sale_order.name)])
            team_id = sale_order.team_id

            if team_id and team_id.id in [1, 2]:
                for rec in purchase_order:
                    for inv in self.search([('invoice_origin', '=', rec.name),('type', 'in', ['in_invoice'])]):
                        for acc_inv in inv.invoice_line_ids:
                            # _logger.info('LINE LINE ' + str(acc_inv.product_id.id) + '==' + product_id)
                            if acc_inv.product_id.id == int(product_id) and acc_inv.quantity != 0.00: #Removed third layer matching for product id.
                                delivery_date = inv.delivery_date
                                cal_date = delivery_date.isocalendar() if delivery_date else cal_date
                                return 'Warenausgang erfolgte KW ' + str(cal_date[1]) + '/' + str(cal_date[0]) if cal_date else cal_date
                for rec in purchase_order:
                    for inv in self.search([('invoice_origin', '=', rec.name),('type', 'in', ['in_invoice'])]):
                        delivery_date = inv.delivery_date
                        cal_date = delivery_date.isocalendar() if delivery_date else cal_date
                        return 'Warenausgang erfolgte KW ' + str(cal_date[1]) + '/' + str(cal_date[0]) if cal_date else cal_date
            else:
                return cal_date
        else:
            return cal_date


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    line_no_stored = fields.Char(string='APos', help="Positionsnummer aus Verkaufsauftrag")

