# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import base64
import zipfile

from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import TemporaryFile, NamedTemporaryFile
from odoo.exceptions import UserError
import csv

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    gteg_file_no = fields.Char(string='GTEG File No')

class GtegProductCode(models.Model):
    _name = 'gteg.product.code'
    _description = 'GTEG Product code'

    name = fields.Char(string='Name', required=1)
    code = fields.Char(string='Code', required=1)
    product_id = fields.Many2one('product.product',string='Product', required=1)

class gteg_wizard_payment(models.TransientModel):
    _name = 'gteg.payment.import'
    _description = 'GTEG payment import'

    csv_file = fields.Binary('Browse File')
    gteg_filename = fields.Char('File name')
    order_id = fields.Many2one("sale.order")
    upload_info = fields.Html("Upload Information")

    @api.onchange('csv_file')
    def filename_change(self):
        self.upload_info = _("<center><h2 style='color:red;'>Please upload .zip file.</h2></center>")
        self.gteg_filename = self.gteg_filename
        if self.gteg_filename:
            try:
                temp = NamedTemporaryFile()
                file_content = {}
                temp.write(base64.b64decode(self.csv_file))
                temp.seek(0)
                with zipfile.ZipFile(temp.name, "r") as f:
                    for name in f.namelist():
                        data = f.read(name)
                        file_content[name] = name
                        file_content[name.split(".")[0] + "__data__"] = data
                csv_data = ""
                for k, v in file_content.items():
                    if k.lower().find(".asc") >= 0:
                        csv_data = file_content.get(k.split(".")[0] + "__data__")
                temp_csv = NamedTemporaryFile()
                temp_csv.write(csv_data)
                upload_info = "<h2 align='center'>Only validated invoice will be processed.</h2><table class='table'><thead><tr><th>Invoice Number</th><th>Invoice Status</th><th>Payment Amount</th><th>Payment Date</th></tr></thead><tbody>"
                with open(temp_csv.name, 'r', encoding="ISO-8859-1") as inp:
                    for row in csv.reader(inp, delimiter=';'):
                        if row[0] == "K":
                            inv_reference = (row[5]).strip() if row[5] else False
                            payment_date = row[25][0:4] + "-" + row[25][4:6] + "-" + row[25][6:8]
                            payment_ammount = int(row[16])/100
                            if inv_reference:
                                avail_invoice = self.env["account.move"].search([('name', 'like', inv_reference)],limit=1)
                                if avail_invoice:
                                    if avail_invoice.state == "posted":
                                        class_info = 'success'
                                    else:
                                        class_info = 'info'
                                else:
                                    class_info = 'danger'
                                upload_info += "<tr class='"+str(class_info)+"'><td>"+inv_reference+"</td><td>" + str((avail_invoice.state +" Invoice ID : "+str(avail_invoice.id)) if avail_invoice else "No Invoice found") + "</td><td>"+str(payment_ammount)+"</td><td>" + str(payment_date) + "</td></tr>"
                upload_info += "</tbody></table>"
                self.upload_info = upload_info
            except Exception as e:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload .zip file.</h2></center>")

    def import_gteg_payment(self):
        try:
            temp = NamedTemporaryFile()
            file_content = {}
            temp.write(base64.b64decode(self.csv_file))
            temp.seek(0)
            with zipfile.ZipFile(temp.name, "r") as f:
                for name in f.namelist():
                    data = f.read(name)
                    file_content[name] = name
                    file_content[name.split(".")[0] + "__data__"] = data
            csv_data = ""
            for k, v in file_content.items():
                if k.lower().find(".asc") >= 0:
                    csv_data = file_content.get(k.split(".")[0] + "__data__")
            temp_csv = NamedTemporaryFile()
            temp_csv.write(csv_data)
            with open(temp_csv.name, 'r', encoding="ISO-8859-1") as inp:
                for row in csv.reader(inp, delimiter=';'):
                    if row[0] == "K":
                        inv_reference = (row[5]).strip() if row[5] else False
                        payment_ammount = int(row[16])/100
                        avail_invoice = self.env["account.move"].search([('name', 'like', inv_reference), ('state', 'in', ['posted'])], limit=1)
                        if avail_invoice:
                            avail_invoice.pay_and_reconcile(self.env['account.journal'].browse([13]), pay_amount=payment_ammount)
        except Exception as e:
            raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))




class gteg_wizard_invoice(models.TransientModel):
    _name = 'gteg.invoice.import'
    _description = 'GTEG Invoice import'

    csv_file = fields.Binary('Browse File')
    gteg_filename = fields.Char('File name')
    order_id = fields.Many2one("sale.order")
    upload_info = fields.Html("Upload Information")

    def _compute_rec_link(self, rec_id, rec_model):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        return '%s/web?db=%s#id=%s&view_type=form&model=%s' % (base_url, database_name, rec_id, rec_model)

    @api.onchange('csv_file')
    def filename_change(self):
        self.upload_info = _("<center><h2 style='color:red;'>Please upload .zip file.</h2></center>")
        self.gteg_filename = self.gteg_filename
        if self.gteg_filename:
            try:
                temp = NamedTemporaryFile()
                file_content = {}
                temp.write(base64.b64decode(self.csv_file))
                temp.seek(0)
                with zipfile.ZipFile(temp.name, "r") as f:
                    for name in f.namelist():
                        data = f.read(name)
                        file_content[name] = name
                        file_content[name.split(".")[0] + "__data__"] = data
                csv_data = ""
                for k, v in file_content.items():
                    if k.lower().find(".asc") >= 0:
                        csv_data = file_content.get(k.split(".")[0] + "__data__")

                f = open("/tmp/temp_invoice", "wb")
                f.write(csv_data)
                f.close()

                upload_info = "<table class='table'><thead><tr><th></th><th>Odoo PO ID</th><th>Invoice Number</th><th>Invoice Date</th></tr></thead><tbody>"
                with open('/tmp/temp_invoice', 'r', encoding="ISO-8859-1") as inp:
                    for row in csv.reader(inp, delimiter=';'):
                        if row[0] == "K":
                            invoice_date = row[7][0:4] + "-" + row[7][4:6] + "-" + row[7][6:8]
                            file_sup_inv_no = str(row[5].strip())
                            file_gteg_inv_no = str(row[6].strip())
                            if file_sup_inv_no == file_gteg_inv_no or not file_sup_inv_no:
                                file_sup_inv_no = self._get_sup_inv_number(file_content, file_gteg_inv_no)
                            inv_name = str(file_sup_inv_no) + ", " + str(file_gteg_inv_no)
                            invoice_id = self.env['account.move'].search([('gteg_file_no', '=', inv_name)])
                            header_name = _("INV Already Imported") if invoice_id else _("INV HEADER")
                            color_style = "background-color: coral;" if invoice_id else "background-color: gold;"
                            supplier_name = str(row[4]) if row[4] else "Interaval"
                            upload_info += "<tr style='"+color_style+"'><td>"+header_name+"</td><td>" + supplier_name + "</td><td>" + str(row[5]) + "</td><td colspan='2'>" + str(invoice_date) + "</td></tr>"
                        elif row[0] == "P":
                            purchase_order = self.env["purchase.order"].search([('name', '=', (row[7]).strip())],limit=1)
                            product_data = False
                            if not purchase_order:
                                po_number = (row[7]).strip().split("/")
                                if len(po_number) >= 3:
                                    purchase_order = self.env["purchase.order"].search([('name', '=', po_number[2])],limit=1)
                            if not purchase_order:
                                po_number = ((row[7]).strip())
                                if len(po_number) == 9:
                                    po_number = self._insert_char_po_number(po_number)
                                    purchase_order = self.env["purchase.order"].search([('name', '=', po_number)], limit=1)
                            if not purchase_order:
                                po_number = ((row[7]).strip())
                                po_number = ''.join(e for e in po_number if e.isdigit())
                                if len(po_number) >= 9:
                                    po_number = self._insert_char_po_number(po_number)[:10]
                                    purchase_order = self.env["purchase.order"].search([('name', '=', po_number)], limit=1)
                            if purchase_order:
                                self._cr.execute("select s.id from product_supplierinfo as s,product_template as p where (s.company_id is null or s.company_id=%s) and s.product_code ='%s' and s.product_tmpl_id=p.id and p.active='t' and s.name=%s limit 1"%(self.env.company.id,(row[13]).strip(),purchase_order.partner_id.id if purchase_order else False))
                                suppinfo_ids = [x[0] for x in self._cr.fetchall()]
                                product_data = self.env["product.supplierinfo"].browse(suppinfo_ids) if suppinfo_ids else False
                            product_qty = int(row[17].strip()) / 10000
                            product_unit_price = int(row[16].strip()) / 100
                            if purchase_order:
                                po_status = "<a href='"+self._compute_rec_link(purchase_order.id,'purchase.order')+"'>"+str(purchase_order.name)+"</a>"
                            else:
                                po_status = "NO PO FOUND"

                            if not product_data:
                                product_data = self._get_transport_product(row[13], return_error_article = False)
                            if product_data:
                                line_name = product_data.product_tmpl_id.product_variant_id.name if product_data.product_tmpl_id.product_variant_id else product_data.product_tmpl_id.name
                                prod_sku = product_data.product_tmpl_id.product_variant_id.default_code if product_data.product_tmpl_id.product_variant_id else product_data.product_tmpl_id.default_code
                                upload_info += "<tr class='info'><td></td><td>"+po_status+"</td><td><a href='"+str(self._compute_rec_link(product_data.product_tmpl_id.product_variant_id.id,'product.product'))+"'> ["+str(prod_sku+ " ] " +line_name)+"</a></td><td>"+str(product_qty)+"</td><td>"+str(product_unit_price)+"</td></tr>"
                            else:
                                upload_info += "<tr class='danger'><td></td><td>"+po_status+"</td><td>" + str((row[13]).strip()) + "</td><td>" + str(product_qty) + "</td><td>" + str(product_unit_price) + "</td></tr>"
                upload_info += "</tbody></table>"
                self.upload_info = upload_info
            except Exception as e:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload .zip file.</h2></center>")

    def _get_transport_product(self, code, return_error_article=True):
        gteg_object = self.env["gteg.product.code"].search([('code', '=', code)], limit=1)
        if return_error_article:
            return gteg_object.product_id if gteg_object else self._get_error_article()
        else:
            return gteg_object.product_id if gteg_object else False

    def _get_error_article(self):
        product_check = self.env["product.product"].sudo().search([('name', '=', 'error article')])
        return product_check if product_check else self.env["product.product"].sudo().create({'name': 'error article', 'sale_ok': True, 'purchase_ok': True})

    def _get_sup_inv_number(self, file_content, gteg_no):
        try:
            for k, v in file_content.items():
                if k.lower().find(gteg_no) >= 0:
                    return k.split("_")[1]
        except:
            return ""

        return ""

    def _insert_char_po_number(self, po_number):
        po_number = list(po_number)
        po_number.insert(2, "-")
        return "".join(po_number)

    def _get_correct_tax(self, tex_percentage):
        if tex_percentage == 0:
            return 3
        elif tex_percentage / 100 == 19:
            return 14
        elif tex_percentage / 100 == 16:
            return 29
        elif tex_percentage / 100 == 7:
            return 15
        elif tex_percentage / 100 == 5:
            return 30
        else:
            return 15

    def import_gteg_invoice(self):
        try:
            temp = NamedTemporaryFile()
            file_content = {}
            temp.write(base64.b64decode(self.csv_file))
            temp.seek(0)
            with zipfile.ZipFile(temp.name, "r") as f:
                for name in f.namelist():
                    data = f.read(name)
                    file_content[name] = name
                    file_content[name.split(".")[0]+"__data__"] = data
            csv_data = ""
            for k,v in file_content.items():
                if k.lower().find(".asc") >= 0:
                    csv_data = file_content.get(k.split(".")[0]+"__data__")

            f = open("/tmp/temp_final_invoice", "wb")
            f.write(csv_data)
            f.close()

            latest_invoice_id = False
            latest_analytic_account = False
            gteg_file_no = False
            invoice_list = []
            with open('/tmp/temp_final_invoice', 'r', encoding="ISO-8859-1") as inp:
                for row in csv.reader(inp, delimiter=';'):
                    if row[0] == "D":
                        gteg_file_no = row[4]
                    if row[0] == "K":
                        invoice_date = row[7][0:4]+"-"+row[7][4:6]+"-"+row[7][6:8]
                        #invoice_date = row[6][0:4] + "-" + row[6][4:6] + "-" + row[6][6:8]
                        file_sup_inv_no = str(row[5].strip())
                        # file_sup_inv_no = str(row[4].strip())
                        file_gteg_inv_no = str(row[6].strip())
                        #file_gteg_inv_no = str(row[5].strip())
                        if file_sup_inv_no == file_gteg_inv_no or not file_sup_inv_no:
                            file_sup_inv_no = self._get_sup_inv_number(file_content, file_gteg_inv_no)
                        inv_name = str(file_sup_inv_no)+", "+str(file_gteg_inv_no)
                        skip_invoice_id = self.env['account.move'].search([('type', 'in', ['in_invoice','in_refund']),('ref', '=', file_sup_inv_no.replace(".","")[:12])])
                        if skip_invoice_id:
                            latest_invoice_id = False
                            continue
                        invoice_id = self.env['account.move'].search([('gteg_file_no', '=', inv_name)])
                        invoice_total_amount = int(row[16].strip())
                        if invoice_id:
                            latest_invoice_id = False
                            continue
                            #invoice_id.invoice_line_ids = [(5, 0, 0)]
                        else:
                            invoice_vals = {
                                "ref": file_sup_inv_no.replace(".","")[:12],#Limited only 12 character due to DATEV export validation.
                                "partner_id": 1,
                                "type":"in_invoice" if invoice_total_amount >= 0 else "in_refund",
                                "invoice_date":invoice_date,
                                "gteg_file_no": inv_name,
                                "name": "/", #inv_name,
                                "journal_id": 2, # TO-DO need to add exact journal id of Incoming invoice journal.
                            }
                            invoice_id = self.env["account.move"].create(invoice_vals)
                        invoice_list.append(invoice_id)
                        latest_invoice_id = invoice_id
                        for k, v in file_content.items():
                            if k.lower().find(row[5].lower()) >= 0 and k.lower().find("__data__") >= 0:
                                attachment_id = self.env["ir.attachment"].sudo().create(
                                    {"res_model": "account.move", "res_id": invoice_id.id, "name":k.replace("__data__",".pdf"),
                                     "datas": base64.encodestring(v),"store_fname" : k, "store_fname" : k.replace("__data__",".pdf")})
                    if row[0] == "P" and latest_invoice_id:
                        delivery_date = row[3][0:4] + "-" + row[3][4:6] + "-" + row[3][6:8]
                        if len(delivery_date) >= 6:
                            latest_invoice_id.delivery_date = delivery_date # Assign invoice delivery date
                        purchase_order = self.env["purchase.order"].search([('name', '=', (row[7]).strip())], limit=1)
                        if not purchase_order:
                            po_number = (row[7]).strip().split("/")
                            if len(po_number) >= 3:
                                purchase_order = self.env["purchase.order"].search([('name', '=', po_number[2])],limit=1)
                        if not purchase_order:
                            po_number = ((row[7]).strip())
                            if len(po_number) == 9:
                                po_number = self._insert_char_po_number(po_number)
                                purchase_order = self.env["purchase.order"].search([('name', '=', po_number)], limit=1)
                        if not purchase_order:
                            po_number = ((row[7]).strip())
                            po_number = ''.join(e for e in po_number if e.isdigit())
                            if len(po_number) >= 9:
                                po_number = self._insert_char_po_number(po_number)[:10]
                                purchase_order = self.env["purchase.order"].search([('name', '=', po_number)], limit=1)
                        latest_invoice_id.partner_id = purchase_order.partner_id if purchase_order else 1
                        latest_invoice_id.account_id = latest_invoice_id.partner_id.property_account_payable_id
                        product_data = False
                        line_description = False
                        if purchase_order:
                            latest_invoice_id.invoice_origin = purchase_order.name
                            purchase_order.invoice_ids = [(4,latest_invoice_id.id)]
                            self._cr.execute("select s.id from product_supplierinfo as s,product_template as p where (s.company_id is null or s.company_id=%s) and s.product_code ='%s' and s.product_tmpl_id=p.id and p.active='t' and s.name=%s limit 1" % (self.env.company.id, (row[13]).strip(),purchase_order.partner_id.id if purchase_order else False))
                            suppinfo_ids = [x[0] for x in self._cr.fetchall()]
                            product_data = self.env["product.supplierinfo"].browse(suppinfo_ids).product_tmpl_id.product_variant_id if suppinfo_ids else False
                        if not product_data:
                            #product_data = self._get_error_article()
                            product_data = self._get_transport_product(row[13])
                            if not self._get_transport_product(row[13], return_error_article=False):
                                line_description = str(row[13])+ " " + str(row[14])
                        if product_data:
                            found_product = product_data
                            product_qty = int(row[17].strip())/10000
                            product_unit_price = int(row[19].strip()) / 10000
                            tax_id = self._get_correct_tax(int(row[21].strip()))
                            line_name = line_description if line_description else found_product.name
                            line_account_id = found_product.property_account_expense_id if found_product.property_account_expense_id else found_product.categ_id.property_account_expense_categ_id
                            # if tax_id in [29,30]: # based on taxes applied fiscal position and account
                                # latest_invoice_id.fiscal_position_id = 16
                                # fpos = self.env["account.fiscal.position"].sudo().browse(16)
                                # accounts = found_product.product_tmpl_id.get_product_accounts(fpos)
                                # if accounts['expense']:
                                #     line_account_id = accounts['expense'].id
                            invoice_line_vals = {
                                "name": line_name, "product_id": found_product.id, "price_unit": product_unit_price,
                                "account_id": line_account_id, "quantity": product_qty,
                                "tax_ids": [(4, tax_id)],
                            }
                            if purchase_order:
                                po_line = purchase_order.order_line.filtered(lambda rec: rec.product_id and rec.product_id.id == found_product.id)
                                if po_line:
                                    invoice_line_vals["analytic_account_id"] = po_line[0].account_analytic_id.id
                                    invoice_line_vals["line_no_stored"] = po_line[0].line_no
                                    latest_analytic_account = invoice_line_vals.get("analytic_account_id")
                                    invoice_line_vals["purchase_line_id"] = po_line[0].id
                            latest_invoice_id.invoice_line_ids = [(0,0,invoice_line_vals)]
                            # if not found_product.ean_number: Odoo13Change
                            #     found_product.ean_number = row[12].strip() if row[12].strip() else ""
                    if row[0] == "R" and latest_invoice_id:
                        gteg_product_code = self._get_transport_product(row[3])
                        if gteg_product_code:
                            found_product = gteg_product_code
                            product_qty = 1
                            product_unit_price = int(row[4].strip()) / 100
                            tax_id = self._get_correct_tax(int(row[5].strip()))
                            line_name = str(row[7].strip())
                            line_prod_id = found_product.id
                            line_account_id = found_product.property_account_expense_id if found_product.property_account_expense_id else found_product.categ_id.property_account_expense_categ_id
                            latest_invoice_id.invoice_line_ids = [(0,0,{"name": line_name, "analytic_account_id":latest_analytic_account, "product_id": line_prod_id, "price_unit": product_unit_price, "account_id": line_account_id, "quantity": product_qty, "tax_ids" : [(4, tax_id)]})]
            for inv in invoice_list:
                inv._recompute_tax_lines()
                try:
                    inv.vendorbill_fix_action(active_ids=[inv.id])
                except:
                    pass
                # if not inv.invoice_line_ids: Odoo13Change
                #     inv.unlink()

        except Exception as e:
            raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
