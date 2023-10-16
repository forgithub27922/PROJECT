	# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@openfellas.com
#
##############################################################################

from openerp import netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv
from openerp.tools.translate import _

import time
from datetime import datetime
from xml.dom import minidom
import re
import zipfile
from io import StringIO,BytesIO
import base64
import logging
from lxml import etree, objectify
from openerp import tools

from openerp import models, fields, api, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError

import logging
_logger = logging.getLogger(__name__)


def _reopen(self, res_id, model, view_id=None):
    if not view_id:
        view_id = 'datev_export.datev_export_view'

    return {'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': res_id,
            'res_model': self._name,
            'view_id': self.env.ref(view_id).id,
            'target': 'new',
            # save original model in context, because selecting the list of available
            # templates requires a model in context
            'context': {
                'default_model': model,
            },
    }


class DatevExportOptions(models.TransientModel):
    _name = "datev.export.options"
    _description = "Export to XML Datev format using options"

    @api.model
    def _get_period(self):
        ids = self.env['account.period'].find()
        if len(ids):
            return ids[0]
        return False

    in_invoice = fields.Boolean(string='Incoming Invoices', default=lambda *a: True)
    out_invoice = fields.Boolean(string='Outgoing Invoices', default=lambda *a: True)
    in_refund = fields.Boolean(string='Incoming Refunds', default=lambda *a: True)
    out_refund = fields.Boolean(string='Outgoing Refunds', default=lambda *a: True)
    date_start = fields.Date(string='From Date', help="Ignored if Period is selected")
    date_stop = fields.Date(string='To Date', help="Ignored if Period is selected")
    # period_id = fields.Many2one('account.period', string='Period', default=_get_period)
    company_id = fields.Many2one('res.company', string='Company', required = True, default=lambda self: self.env['res.users'].browse(self._uid).company_id.id)
    datev_file = fields.Binary(string='.zip File', readonly = True)
    datev_filename = fields.Char(string='Filename', size=64, readonly=True, default=lambda *a: 'xml.zip')
    state = fields.Selection([('choose','choose'),('get','get')], string='State', default=lambda *a: 'choose')
    response_message = fields.Text(string='Response Message', readonly=True)

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def do_export_file(self):
        self.ensure_one()
        logging.getLogger('DATEV EXPORT').warn("Begin of export with options"+str(self._context))
        if self._context is None:
            context = {}
        wizard = self
        company_id = wizard.company_id.id
        invoice_type_list = []
        if wizard.in_invoice:
            invoice_type_list.append('in_invoice')
        if wizard.out_invoice:
            invoice_type_list.append('out_invoice')
        if wizard.in_refund:
            invoice_type_list.append('in_refund')
        if wizard.out_refund:
            invoice_type_list.append('out_refund')
        if not len(invoice_type_list):
            raise ValidationError(_('Please check at least one invoice type to export'))
        inv_obj = self.env['account.move']
        if wizard.date_start:
            if wizard.date_stop:
                # invoice_ids = inv_obj.search([('state','in',['open','posted']),('exported_to_datev','=',False),('invoice_date','>=',wizard.date_start),('invoice_date','<=',wizard.date_stop),('type','in',invoice_type_list),('company_id','=',company_id)])
                invoice_ids = inv_obj.sudo().search([('state', 'in', ['open', 'posted']), ('exported_to_datev', '=', False),
                                              ('invoice_date', '>=', wizard.date_start),
                                              ('invoice_date', '<=', wizard.date_stop),
                                              ('type', 'in', invoice_type_list)])
            else:
                # invoice_ids = inv_obj.search([('state','in',['open','posted']),('exported_to_datev','=',False),('invoice_date','>=',wizard.date_start),('type','in',invoice_type_list),('company_id','=',company_id)])
                invoice_ids = inv_obj.sudo().search([('state', 'in', ['open', 'posted']), ('exported_to_datev', '=', False),
                                              ('invoice_date', '>=', wizard.date_start),
                                              ('type', 'in', invoice_type_list)])
        else:
            raise ValidationError(_('Please select at least Start Date'))
        logging.getLogger('DATEV EXPORT').warn("Invoices "+str(invoice_ids._ids))
        zip_file, res_msg = self.env['datev.export'].generate_zip(invoice_ids._ids)
        ret= {
            'company_id': self.env['res.users'].browse(self._uid).company_id.id,
            'datev_file': zip_file,
            'datev_filename': time.strftime('%Y_%m_%d_%H_%M')+'_xml.zip',
            'state': 'get',
            'response_message': res_msg,
            'invoice_ids': invoice_ids,
            }

        res = self.write(ret)
        logging.getLogger('DATEV EXPORT').warn("End of export with options"+str(self._context)+" IDS: "+str(self._ids)+ " RES: "+str(res))
        record = self.browse(self._ids[0])
        return _reopen(self, record.id, 'datev.export.options', view_id='datev_export.view_datev_export_options')

class DatevExport(osv.osv_memory):
    _name = "datev.export"
    _description = "Export to XML Datev format"

    file = fields.Binary(string='.zip File', readonly = True)
    filename = fields.Char(string='Filename', size=64, readonly=True)
    state = fields.Selection([('choose','choose'),('get','get')], string='State', default='choose')
    response_message = fields.Text(string='Response Message', readonly=True)

    @api.model
    def toprettyxml_fixed(self, input_string):
        fix = re.compile(r'((?<=>)(\n[\t]*)(?=[^<\t]))|(?<=[^>\t])(\n[\t]*)(?=<)')
        return re.sub(fix, '', input_string.decode("utf-8"))

    @api.model
    def createTextElement(self, doc, parent_element, element, text):
        text_element = doc.createElement(element)
        parent_element.appendChild(text_element)
        text_node = doc.createTextNode(text)
        text_element.appendChild(text_node)
        return True

    @api.model
    def include_doc_header(self, doc, company):
        archive = doc.createElement("archive")
        doc.appendChild(archive)
        archive.setAttribute("version", "3.0")
        archive.setAttribute("generatingSystem", "OpenERP")
        archive.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        archive.setAttribute("xsi:schemaLocation", "http://xml.datev.de/bedi/tps/document/v03.0 document_v030.xsd")
        archive.setAttribute("xmlns", "http://xml.datev.de/bedi/tps/document/v03.0")
        header = doc.createElement("header")
        archive.appendChild(header)

        # Grimm START
        company = self.env["res.company"].sudo().browse(1)
        # Grimm END

        self.createTextElement(doc, header, "date", time.strftime('%Y-%m-%dT%H:%M:%S'))
        self.createTextElement(doc, header, "description", company.name + " Accounting")
        if company.consultant_number:
            self.createTextElement(doc, header, "consultantNumber", company.consultant_number)
        if company.consultant_number:
            self.createTextElement(doc, header, "clientNumber", company.client_number)
        self.createTextElement(doc, header, "clientName", company.name)
        return archive

    @api.model
    def set_address(self, address, inv_address):
        if not (inv_address.zip and inv_address.city and inv_address.name):
             raise ValidationError(_('Address of partner %s must have Name, Zip and City') % inv_address.name)
        if inv_address.street:
            address.setAttribute("street",inv_address.street[:41])
        address.setAttribute("zip",inv_address.zip)
        address.setAttribute("city",inv_address.city[:30])
        address.setAttribute("name",inv_address.name[:50])
        if inv_address.country_id and inv_address.country_id.code:
            address.setAttribute("country",inv_address.country_id.code)

    @api.model
    def set_bucode(self, inv, element, line):
        # bu_code_element = inv.createElement("bu_code")
        # element.appendChild(bu_code_element)
        bu_code = "%s" % (line._calculate_bu_code() or '0')
        # bu_code_element.setAttribute('bu_code', bu_code)
        company_account_export_bu_code = line.company_id and line.company_id.export_for_checked_or_not_checked_acc_bu_code_to_datev
        if company_account_export_bu_code:
            line_account_export_bu_code = line.account_id and line.account_id.export_bu_code_to_datev
        else:
            line_account_export_bu_code = line.account_id and not line.account_id.export_bu_code_to_datev
        if line.tax_ids and bu_code not in ['00'] and line_account_export_bu_code:
            element.setAttribute('bu_code', bu_code)

    @api.model
    def set_costcategoryid(self, inv, element, line):
        export_analytic_account = line and line.company_id and line.company_id.export_cost_category_id or False
        cost_category_id = line and line.analytic_account_id and line.analytic_account_id.code or False
        _logger.info(_("DATEV SET COST CATEGORY: AA %s, CC %s!") % (export_analytic_account, cost_category_id))
        if export_analytic_account and cost_category_id:
            element.setAttribute('cost_category_id', cost_category_id)

    @api.model
    def include_invoice_line(self, line, inv, invoice_el, invoice_sign = 1):
        invoice_item_list = inv.createElement("invoice_item_list")
        invoice_el.appendChild(invoice_item_list)
        # TODO
        # error with uos when no product in invoice.line
        uos_name = line.product_uom_id.name
        if not uos_name: uos_name = u'Stück'
        invoice_item_list.setAttribute("order_unit", uos_name)
        invoice_item_list.setAttribute("net_product_price", "%.3f"%(line.price_unit * invoice_sign) or "")
        line.product_id.default_code and invoice_item_list.setAttribute("product_id", line.product_id.default_code)
        invoice_item_list.setAttribute("quantity", "%.2f"%(line.quantity))
        if not line.product_id or not line.name:
            raise ValidationError(_("Es gibt kein Produkt in einer Zeile von %s Rechnung"%line.move_id.name))
        invoice_item_list.setAttribute("description_short", line.product_id and line.product_id.name[:40] or line.name[:40])

        price_line_amount = inv.createElement("price_line_amount")
        invoice_item_list.appendChild(price_line_amount)
        price_line_amount.setAttribute("currency", line.move_id.currency_id.name)
        if not line.tax_ids or line.move_id.amount_tax == 0:
            tax_rate = 0
            tax_amount = False
            tax_ammount_unsigned = 0
        else:
            tax_rate = line.tax_ids[0].amount

            u_price = line.quantity and line.price_subtotal/line.quantity or 0
            tax = line.tax_ids.compute_all(u_price, line.move_id.currency_id, line.quantity, line.product_id, line.move_id.partner_id.commercial_partner_id)['taxes']
            tax_ammount_unsigned = tax[0]['amount']
            tax_amount = tax[0]['amount'] * invoice_sign

        price_line_amount.setAttribute("tax", "%.2f"%(tax_rate))
        if tax_amount:
            tax_amount = round(tax_amount, 2)
        tax_amount and price_line_amount.setAttribute("tax_amount", "%.2f"%(tax_amount))
        price_line_amount.setAttribute("net_price_line_amount", "%.2f"%(line.price_subtotal * invoice_sign))

        discount_sign = 1 if line.price_subtotal >= 0 else -1

        price_line_amount.setAttribute("gross_price_line_amount", "%.2f" % ((abs(line.price_subtotal) + abs(tax_ammount_unsigned)) * discount_sign * invoice_sign))

        accounting_info = inv.createElement("accounting_info")
        invoice_item_list.appendChild(accounting_info)
        line.account_id.code and accounting_info.setAttribute("account_no", self.line_account_code(line.account_id.code))
        self.set_bucode(inv, accounting_info, line) # Activated BU code
        self.set_costcategoryid(inv, accounting_info, line)
        line.account_id.name and accounting_info.setAttribute("booking_text", line.account_id.name[:30])

        # if line.move_id and line.move_id.delivery_date_start and line.move_id.delivery_date_end:
        #     delivery_period = inv.createElement("delivery_period")
        #     invoice_item_list.appendChild(delivery_period)
        #     delivery_period.setAttribute("delivery_date_start", line.move_id.delivery_date_start)
        #     delivery_period.setAttribute("delivery_date_end", line.move_id.delivery_date_end)

        return tax_rate

    # def _get_grimm_account(self, move_line):
    #     move_line = move_line.with_context(force_company=1)
    #     if not move_line.product_id:
    #         return
    #     fiscal_position = move_line.move_id.fiscal_position_id
    #     accounts = move_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
    #     if move_line.move_id.is_sale_document(include_receipts=True):
    #         # Out invoice.
    #         return self.line_account_code(accounts['income'].code or move_line.account_id.code)
    #     elif move_line.move_id.is_purchase_document(include_receipts=True):
    #         # In invoice.
    #         return self.line_account_code(accounts['expense'].code or move_line.account_id.code)


    @api.model
    def line_account_code(self, code):
        res_code = code and code.lstrip('0') or ''
        return res_code

    @api.model
    def pick_done_last(self, pickings):
        last_date = datetime.min
        for pick in pickings:
            if pick.state == 'done' and datetime.strptime(pick.date_done, '%Y-%m-%d %H:%M:%S') > last_date:
                last_date = datetime.strptime(pick.date_done, '%Y-%m-%d %H:%M:%S')
        if last_date != datetime.min:
            return datetime.strftime(last_date, '%Y-%m-%d')
        else:
            return False

    @api.model #Odoo13Change
    def refunded_inv_search(self, invoice):
        drawee_no = False
        for move in invoice.payment_move_line_ids:
            if move.matched_credit_ids:
                for matched_credit in move.matched_credit_ids:
                    for creadit_move in matched_credit.credit_move_id:
                        if creadit_move.invoice_id and creadit_move.invoice_id.id != invoice.id:
                            drawee_no = creadit_move.move_id.name
                            break

                    for debit_move in matched_credit.debit_move_id:
                        if debit_move.invoice_id and debit_move.invoice_id.id != invoice.id:
                            drawee_no = debit_move.move_id.name
                            break
            if drawee_no:
                break
            if move.matched_debit_ids:
                for matched_debit in move.matched_debit_ids:
                    for creadit_move in matched_debit.credit_move_id:
                        if creadit_move.invoice_id and creadit_move.invoice_id.id != invoice.id:
                            drawee_no = creadit_move.move_id.name
                            break
                    for debit_move in matched_debit.debit_move_id:
                        if debit_move.invoice_id and debit_move.invoice_id.id != invoice.id:
                            drawee_no = debit_move.move_id.name
                            break
            if drawee_no:
                break
        return drawee_no

    @api.model
    def tax_rate_find(self, tax, tax_rates):
        calc_rate = 100 * tax.amount / tax.invoice_id.amount_untaxed
        rate_diff = calc_rate
        line_rate = tax_rates[0]
        for rate in tax_rates:
            if rate_diff > abs(calc_rate - rate):
                rate_diff = abs(calc_rate - rate)
                line_rate = rate
        return line_rate

    @api.model
    def include_discount_line(self, invoice, pay_term_line, payment_conditions):
        return True

    @api.model
    def get_bp_account_no(self, invoice):
        bp_account_no = invoice.l10n_de_datev_main_account_id.code or ""
        return bp_account_no

    @api.model
    def include_invoice(self, invoice, our_invoice_address, our_vat_id):
        inv = minidom.Document()
        invoice_el = inv.createElement("invoice")
        inv.appendChild(invoice_el)

        invoice_el.setAttribute("generator_info", invoice.company_id.name)
        # Grimm START
        grimm_company = self.env["res.company"].sudo().browse(1)
        if grimm_company:
            invoice_el.setAttribute("generator_info", grimm_company.name)
        # Grimm END
        invoice_el.setAttribute("generating_system", "OpenERP")
        invoice_el.setAttribute("description", "DATEV Import invoices")
        invoice_el.setAttribute("version", "3.0")
        invoice_el.setAttribute("xml_data", "Kopie nur zur Verbuchung berechtigt nicht zum Vorsteuerabzug") # new in v3
        invoice_el.setAttribute("xsi:schemaLocation","http://xml.datev.de/bedi/tps/invoice/v030 Belegverwaltung_online_invoice_v030.xsd")
        invoice_el.setAttribute("xmlns","http://xml.datev.de/bedi/tps/invoice/v030")
        invoice_el.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance")

        if invoice.type in ['out_invoice','in_invoice']:
            invoice_type = "Rechnung"
            invoice_sign = 1
            if invoice.type == 'out_invoice':
                invoice_num = invoice.name
                drawee_no = False
            else:
                invoice_num = invoice.ref #invoice.reference
                drawee_no = invoice.name or ''
        else:
            invoice_type = "Gutschrift/Rechnungskorrektur"
            invoice_sign = -1
            # drawee_no = self.refunded_inv_search(invoice)
            if invoice.type == 'out_refund':
                invoice_num = invoice.name
                drawee_no = False
            else:
                invoice_num = invoice.ref  #invoice.reference
                drawee_no = invoice.name

        if invoice.type in ['out_invoice','out_refund']:
            we_are_supplier = True
            recipient_address_obj = invoice.partner_id.commercial_partner_id
            recipient_vat_id = invoice.partner_id.commercial_partner_id.vat
            issuer_address_obj = our_invoice_address.commercial_partner_id
            issuer_vat_id = our_vat_id
        else:
            we_are_supplier = False
            issuer_address_obj = invoice.partner_id.commercial_partner_id
            issuer_vat_id = invoice.partner_id.commercial_partner_id.vat
            recipient_address_obj = our_invoice_address.commercial_partner_id
            recipient_vat_id = our_vat_id

        invoice_info = inv.createElement("invoice_info")
        invoice_el.appendChild(invoice_info)
        invoice_info.setAttribute("invoice_type", invoice_type)
        invoice_info.setAttribute("invoice_date", str(invoice.invoice_date))
        delivery_date = False
        if invoice.delivery_date:
            delivery_date = invoice.delivery_date
        else:
            delivery_date = invoice.invoice_date
        invoice_info.setAttribute("delivery_date",  str(delivery_date))
        invoice_info.setAttribute("invoice_id", invoice_num) #invoice.number
        drawee_no and invoice_info.setAttribute("drawee_no",drawee_no)

        if invoice.delivery_date_start and invoice.delivery_date_end:
            delivery_period = inv.createElement("delivery_period")
            invoice_el.appendChild(delivery_period)
            delivery_period.setAttribute("delivery_date_start", str(invoice.delivery_date_start))
            delivery_period.setAttribute("delivery_date_end", str(invoice.delivery_date_end))

        invoice_party = inv.createElement("invoice_party")
        invoice_el.appendChild(invoice_party)
        recipient_vat_id and invoice_party.setAttribute("vat_id",recipient_vat_id)
        party_address = inv.createElement("address")
        invoice_party.appendChild(party_address)
        self.set_address(party_address, recipient_address_obj)

        supplier_party = inv.createElement("supplier_party")
        invoice_el.appendChild(supplier_party)
        issuer_vat_id and supplier_party.setAttribute("vat_id",issuer_vat_id)
        supp_address = inv.createElement("address")
        supplier_party.appendChild(supp_address)
        self.set_address(supp_address, issuer_address_obj)
        if invoice.invoice_partner_bank_id:
            account = inv.createElement("account")
            supplier_party.appendChild(account)
            # invoice.invoice_partner_bank_id.acc_number and account.setAttribute("bank_account", invoice.invoice_partner_bank_id.acc_number)
            # hasattr(invoice.invoice_partner_bank_id.bank_id, 'bic') and account.setAttribute("bank_code", invoice.invoice_partner_bank_id.bank_id.bic)
            account.setAttribute("bank_name", invoice.invoice_partner_bank_id.bank_id.name[27:] if invoice.invoice_partner_bank_id.bank_id.name and len(invoice.invoice_partner_bank_id.bank_id.name) > 27 else invoice.invoice_partner_bank_id.bank_id.name)
            invoice.invoice_partner_bank_id.bank_id.country.code and account.setAttribute("bank_country", invoice.invoice_partner_bank_id.bank_id.country.code)
            invoice.invoice_partner_bank_id.acc_type == 'iban' and account.setAttribute("iban", invoice.invoice_partner_bank_id.acc_number and invoice.invoice_partner_bank_id.acc_number.replace(' ','') or '')
            hasattr(invoice.invoice_partner_bank_id.bank_id, 'bic') and account.setAttribute("swiftcode", invoice.invoice_partner_bank_id.bank_id.bic)
        booking_info_bp = inv.createElement("booking_info_bp")
        bp_account_no = self.get_bp_account_no(invoice)
        booking_info_bp.setAttribute("bp_account_no", bp_account_no)
        if we_are_supplier:
            invoice_party.appendChild(booking_info_bp)
        else:
            supplier_party.appendChild(booking_info_bp)

        tax_rates = []
        for line in invoice.invoice_line_ids:
            if not line.tax_ids or line.move_id.amount_tax == 0:
                tax_rate = 0
            else:
                tax_rate = line.tax_ids[0].amount
            if not tax_rate in tax_rates:
                tax_rates.append(tax_rate)

        if invoice.invoice_payment_term_id:
            total = invoice.amount_total * invoice_sign
            residual = total
            current_amount = 0
            for pay_term_line in invoice.invoice_payment_term_id.line_ids:    # TODO check if payment done date and amount fields should be added.
                payment_conditions = inv.createElement("payment_conditions")
                invoice_el.appendChild(payment_conditions)
                payment_conditions.setAttribute("currency",invoice.currency_id.name)
                pay_term_line_date_due = str(invoice.invoice_date_due)
                payment_conditions.setAttribute("due_date",pay_term_line_date_due)

                code = 'de_DE'
                lang_pooler = self.env['res.lang']
                term_line_string = ''
                if not lang_pooler.search([('code', '=', code)]):
                    lang_ids = lang_pooler.search([])
                    # code = lang_pooler.browse(lang_ids[0]).code
                    code = lang_ids[0].code

                gn = '-'
                term_line_value =  dict(self.env['account.payment.term.line'].fields_get()['value']['selection'])[pay_term_line.value]
                term_line_string += invoice.invoice_payment_term_id.name
                if len(term_line_string) > 0:
                    term_line_string += gn+term_line_value
                if pay_term_line.value_amount:
                    term_line_string += gn+str(pay_term_line.value_amount)
                term_line_string += gn+str(pay_term_line.days)

                payment_conditions.setAttribute("payment_conditions_text", term_line_string ) # Mandatory when payment term
                self.include_discount_line(invoice, pay_term_line, payment_conditions)

        for line in invoice.invoice_line_ids:
            if line.price_unit * invoice_sign != 0 and line.quantity != 0:
                self.include_invoice_line(line, inv, invoice_el, invoice_sign)

        total_amount = inv.createElement("total_amount")
        invoice_el.appendChild(total_amount)
        total_amount.setAttribute("net_total_amount","%.2f"%(invoice.amount_untaxed * invoice_sign))
        total_amount.setAttribute("currency",invoice.currency_id.name)
        total_amount.setAttribute("total_gross_amount_excluding_third-party_collection","%.2f"%(invoice.amount_total * invoice_sign))

        if invoice.amount_tax == 0.0:
            tax_line = inv.createElement("tax_line")
            total_amount.appendChild(tax_line)
            tax_line.setAttribute("currency",invoice.currency_id.name)
            tax_line.setAttribute("gross_price_line_amount","%.2f"%(invoice.amount_total * invoice_sign))
            tax_line.setAttribute("tax", "0.00")
            tax_line.setAttribute("net_price_line_amount","%.2f"%(invoice.amount_untaxed * invoice_sign))
        else:
            invoice._compute_invoice_taxes_by_group()

            # for tax in invoice.tax_line_ids: #Odoo13Change In odoo13 they removed tax line ids so used amount_by_group field
            #     if (tax.invoice_id.amount_untaxed != 0 and (tax.invoice_id.amount_untaxed+tax.amount)!=0 and tax.amount != 0):
            #         tax_line = inv.createElement("tax_line")
            #         total_amount.appendChild(tax_line)
            #
            #         line_rate = 0.0
            #         if tax.invoice_id.amount_untaxed != 0:
            #             line_rate = self.tax_rate_find(tax, tax_rates)
            #         tax_line.setAttribute("tax", "%.2f"%(line_rate))
            #         tax_line.setAttribute("tax_amount","%.2f"%(tax.amount * invoice_sign))
            #         tax_line.setAttribute("net_price_line_amount","%.2f"%(tax.invoice_id.amount_untaxed * invoice_sign))
            #         tax_line.setAttribute("currency",invoice.currency_id.name)
            #         gross_price_line_amount = (invoice.amount_untaxed+tax.amount) * invoice_sign
            #         tax_line.setAttribute("gross_price_line_amount","%.2f" % gross_price_line_amount)

            # print("After calculation value is ===> ", invoice.amount_by_group)
            for tax_l in invoice.amount_by_group:
                tax_line = inv.createElement("tax_line")
                total_amount.appendChild(tax_line)
                line_rate = 0.0
                if invoice.amount_untaxed != 0:
                    line_rate = (tax_l[1] * 100) / tax_l[2]
                tax_line.setAttribute("tax", "%.2f" % (line_rate))
                tax_line.setAttribute("tax_amount", "%.2f" % (tax_l[1] * invoice_sign))
                tax_line.setAttribute("net_price_line_amount", "%.2f" % (tax_l[2] * invoice_sign))
                tax_line.setAttribute("currency", invoice.currency_id.name)
                gross_price_line_amount = (tax_l[1] + tax_l[2]) * invoice_sign
                tax_line.setAttribute("gross_price_line_amount", "%.2f" % gross_price_line_amount)

        inv_xml= inv.toprettyxml(indent="\t", newl="\n", encoding = "utf-8")
        self.check_xml_file(inv_xml, doc_name = invoice.name)
        return self.toprettyxml_fixed(inv_xml)

    @api.model
    def generate_zip(self, invoice_ids = []):
        if self._context is None:
            context = {}

        logging.getLogger('DATEV EXPORT').warn("Beginning of generate_zip"+str(self._context))
        inv_obj = self.env['account.move']
        if invoice_ids:
            active_ids = invoice_ids
        else:
            active_ids = self._context and self._context.get('active_ids', [])
        records = inv_obj.sudo().search([('id','in',active_ids)])

        active_ids = inv_obj.sudo().search([('id','in',active_ids),('state','in',['posted','open']),('type','!=','entry'),('exported_to_datev', '=', False),('amount_total', '<>', 0)])
        if len(active_ids) == 0:
            raise ValidationError(_("Only invoices in state 'Open' or 'Paid' and not exported Invoices can be exported! There is not even one invoice to be exported!"))
        invoices = active_ids

        company = invoices[0].company_id
        company = self.env["res.company"].sudo().browse(1)
        # res =  self.env['res.partner'].address_get([company.partner_id.id])
        res = company.partner_id.address_get(adr_pref=['invoice'])
        # res =  self.pool['res.partner'].address_get(self._cr, self._uid, [company.partner_id.id], adr_pref=['invoice'], context=self._context)
        # logging.getLogger('DATEV EXPORT').info("Return result of partner is ===> "+str(company.partner_id.address_get(adr_pref=['invoice'])))
        our_invoice_addr_id = res['invoice']
        our_invoice_address = self.env['res.partner'].browse(our_invoice_addr_id)
        our_vat_id = False

        #s=StringIO()
        s = BytesIO()
        zip = zipfile.ZipFile(s, 'w')

        doc = minidom.Document()
        archive = self.include_doc_header(doc, company)
        content = doc.createElement("content")
        archive.appendChild(content)

        not_exported = []
        # response_message = _('Invoices successfully exported! \n')
        response_message = ''
        first_not_ok = True
        for invoice in invoices:
            inv_number = invoice.name.replace('/','')
            if invoice.type in ['out_invoice','out_refund']:
                type = "Outgoing"
                doctype = "2"
                ok, inv_pic = self.create_report([invoice.id])
                if ok:
                    fname = inv_number + ".pdf"
                    # self.add_to_zip(fname, inv_pic, zip)
                else:
                    res_msg = _("Invoice %s have been skipped because report coudn't be generated!") % invoice.name
                    response_message = '%s \n %s' % (response_message, res_msg)
                    not_exported.append(invoice.id)
                    continue
            else:
                type = "Incoming"
                doctype = "2"
                ok = False
                ok, fname, inv_pic = self.get_attachment(invoice)
                if ok:
                    fname = inv_number+"_"+fname
                else:
                    res_msg = _('Invoice %s have been skipped because attachemnt is missing!') % invoice.name
                    response_message = '%s \n %s' % (response_message, res_msg)
                    not_exported.append(invoice.id)
                    continue

            if not invoice.partner_id.commercial_partner_id or not invoice.partner_id.commercial_partner_id.name:
                res_msg = _('Invoice %s have been skipped because partner is missing or partner address has to have official company name!') % invoice.name
                response_message = '%s \n %s' % (response_message, res_msg)
                not_exported.append(invoice.id)
                continue
                # raise ValidationError(_('You have to fill the address for partner of invoice %s. The partner address has to have official company name!') % invoice.number)

            if (invoice.amount_total != 0):
                #try:
                inv_xml = self.include_invoice(invoice, our_invoice_address, our_vat_id)
                self.add_to_zip(inv_number+".xml", inv_xml, zip)
                #except Exception as e:
                #    _logger.info(_("DATEV EXPORT SKIPPED: Invoice %s, error: %s! =========>") % (invoice.number, str(e)))
                #    res_msg = _('Invoice %s have been skipped because Address of partner %s must have Name, Zip and City!') % (invoice.number, our_invoice_address.name)
                #    response_message = '%s \n %s' % (response_message, res_msg)
                #    not_exported.append(invoice.id)
                #    continue

            document = doc.createElement("document")
            content.appendChild(document)

            if ok:
                self.add_to_zip(fname, inv_pic, zip)

            self.createTextElement(doc, document, "description", invoice.name)
            # if not invoice.partner_id or not invoice.partner_id.name:
            #     raise ValidationError(_('You have to fill the address for partner of invoice %s. The partner address has to have official company name!') % invoice.number)

            self.createTextElement(doc, document, "keywords", invoice.partner_id.commercial_partner_id.name + ", " + invoice.name)
            extension = doc.createElement("extension")
            document.appendChild(extension)
            extension.setAttribute("xsi:type","Invoice")
            extension.setAttribute("datafile",inv_number+".xml")
            property = doc.createElement("property")
            extension.appendChild(property)
            property.setAttribute("key","InvoiceType")
            property.setAttribute("value",type)
            if ok:
                extension = doc.createElement("extension")
                document.appendChild(extension)
                extension.setAttribute("xsi:type","File")
                extension.setAttribute("name",fname)

        invoice_ids = map(lambda x: x.id, invoices)
        if not (set(invoice_ids) - set(not_exported)):
            response_message = '%s %s' % (_('There are no Invoices that can be exported! \n'), response_message)
            return False, response_message
            # raise ValidationError(_(response_message))

        doc_xml= doc.toprettyxml(indent="\t", newl="\n", encoding = "utf-8")
        doc_xml= self.toprettyxml_fixed(doc_xml)
        self.check_xml_file(doc_xml, doc_name = "Document.xml", doc = True)
        self.add_to_zip("document.xml", doc_xml, zip)

        zip.close()
        zip_file = base64.encodestring(s.getvalue())
        s.close()
        for invoice in invoices:
            if invoice.id not in not_exported:
                invoice.write({'exported_to_datev': True})

        response_message = '%s %s' % (_('Invoices successfully exported! \n'), response_message)

        logging.getLogger('DATEV EXPORT').warn("End of generat_zip"+str(self._context))
        return zip_file, response_message

    @api.model
    def add_to_zip(self, name, data, zip):
        info = zipfile.ZipInfo(name, date_time=time.localtime(time.time()))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 2175008768
        if not data:
            data = ''
        logging.getLogger('DATEV EXPORT').warn(name+"Type of data is ===>"+str(type(data))+" Type of info ===> "+str(type(info))+" Type of zip is ==> "+str(type(zip)))
        zip.writestr(info,data)
        return True

    def do_export_file(self):
        self.ensure_one()
        invoice_ids = self._context['active_ids']
        zip_file, res_msg = self.env['datev.export'].generate_zip(invoice_ids)
        ret= {
            #'company_id': self.env.user.company_id.id,
            'file': zip_file,
            'filename': time.strftime('%Y_%m_%d_%H_%M')+'_xml.zip',
            'state': 'get',
            'response_message': res_msg,
            'invoice_ids': invoice_ids,
            }
        res = self.write(ret)

        return _reopen(self, self.id, 'datev.export', view_id='datev_export.datev_export_view')

    @api.model
    def get_attachment(self, invoice):
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.search([('res_model','=','account.move'),('res_id','=',invoice.id),('type','=','binary')])
        for attachment in attachment_id:
            # if (attachment.datas_fname.find('signed')!=-1):
            result = base64.decodestring(attachment.datas)
            file_name = attachment.name
            if attachment.mimetype == "application/pdf":
                file_name = attachment.name.replace("__data__",".pdf")
            return (True, file_name, result)

        return (False, False, "No file")

    @api.model
    def create_report(self, ids):
        if not ids:
            return (False, Exception('Report name and Resources ids are required !!!'))
        try:
            # (result, format) = self.pool['report'].get_pdf(self._cr, self._uid, ids, self.env['ir.config_parameter'].get_param('datev_export.invoice_report', default=False)), 'pdf'
            report_id = self.env['ir.actions.report'].sudo().search([('report_name', '=', self.env['ir.config_parameter'].get_param('datev_export.invoice_report', default=False))])
            if len(report_id) > 1:
                report_id = report_id[0]
            (result,format) = report_id.render_qweb_pdf(ids)
        except Exception as e:
            # print('Exception in create report:',e)
            raise ValidationError("Error to print report ===> "+str(e))
            return (False, str(e))
        return (True, result)

    @api.model
    def check_xml_file(self, xml_file, doc_name, doc = False):
    # TODO take the xsd from url online
        return True
        if doc:
            f_schema = tools.file_open('Document_v030.xsd',subdir='addons/datev_export/xsd_files')
        else:
            f_schema = tools.file_open('Belegverwaltung_online_invoice_v030.xsd',subdir='addons/datev_export/xsd_files')
        schema_doc = etree.parse(f_schema)
        schema = etree.XMLSchema(schema_doc)
        parser = etree.XMLParser(schema = schema)
        #_logger.info(_("GRIMM DEBUGGER  %s, error: %s!") % (str(xml_file), str(parser)))
        try:
            doc = etree.fromstring(xml_file, parser)
        except etree.XMLSyntaxError as e:
            raise ValidationError(_("Try to solve the problem with document '%s' according to message below:\n\n%s") % (xml_file, e.msg))
        return True


