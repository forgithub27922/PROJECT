# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dipak Suthar
#    Copyright 2019 Grimm Gastrobedarf.de
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
from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import TemporaryFile, NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)

class product_map_advance(models.TransientModel):
    _name = 'product.map.advance'
    _description = 'Product map advance'

    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        help="""Field from Product Template.""", domain=[('model_id.model', '=', "product.template"),('ttype', 'not in', ['one2many', 'many2many', 'monetory'])])
    #field_value = fields.Char("Value")
    import_id = fields.Many2one('product.create.import')
class SparepartPropertryLine(models.TransientModel):
    _name = "sparepart.property.line"
    _description = 'Sparepart property ine'
    _rec_name = 'attribute_id'

    import_id = fields.Many2one('product.create.import', 'Product Template', ondelete='cascade', required=True)
    attribute_id = fields.Many2one('product.attribute', 'Attribute', ondelete='restrict', required=True)
    value_ids = fields.Many2many('product.attribute.value', string='Attribute Values')

class product_create_import(models.TransientModel):
    _name = 'product.create.import'
    _description = 'Product create import'

    is_advance_mapping = fields.Boolean("Advance Mapping")
    name_from_file = fields.Boolean("Update Name from File", default=True)
    price_from_file = fields.Boolean("Update Price from File", default=True)
    need_override = fields.Boolean("Update if Available", help="This option will searh product based on Internal Reference. If product found ! Update it otherwise create new one based on template product.")
    product_id = fields.Many2one(
        'product.template',
        string='Template Product',
        help="""This is template product so based on this product all product will be created."""
    )
    upload_info = fields.Html("Upload Information", readonly=True)
    #field_map_ids = fields.One2many('product.map.advance', 'import_id', string='Get Original value from product template')
    field_map_ids = fields.Many2many(comodel_name='ir.model.fields', string='Get Original value from product template', domain=[('model_id.model', '=', "product.template"),('ttype', 'not in', ['one2many'])])
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help="""Override company detail if you want."""
    )
    prefix_code = fields.Char("Prefix Code")
    property_set_id = fields.Many2one('property.set', string="Property Set")
    property_set_attribute_ids = fields.Many2many(related='property_set_id.product_attribute_ids',
                                                  string="Property Attribute")
    shopware_property_ids = fields.One2many('sparepart.property.line', 'import_id', 'Shopware Property')
    income_account_id = fields.Many2one(
        'account.account',
        string='Income Account',
        help="""Income Account for this product."""
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        help="""Expense Account for this product."""
    )
    price_account_id = fields.Many2one(
        'account.account',
        string='Price Difference Account',
        help="""Price Difference Account for this product."""
    )
    product_brand_id = fields.Many2one(
        'grimm.product.brand',
        string='Product Brand',
        help="""Set default Product Brand."""
    )
    source_company_id = fields.Many2one(
        'res.company',
        string='Source Company',
        help="""Using this company product template will be copied."""
    )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        help="""Select supplier to add."""
    )
    categ_id = fields.Many2one(
        'product.category',
        string='Product category',
        help="""Override product category if you want."""
    )
    shopware_categ_ids = fields.Many2many(comodel_name='product.category', string='Shopware Categories')
    csv_file = fields.Binary('Browse File')
    filename = fields.Char('File name')

    @api.onchange('product_id')
    def product_id_change(self):
        self.company_id = self.product_id.company_id
        self.source_company_id = self.product_id.company_id

    def create_temp_file(self, csv_data):
        temp = NamedTemporaryFile()
        temp.write(base64.b64decode(csv_data))
        temp.seek(0)
        return temp

    #@api.onchange('csv_file')
    def filename_change(self):
        self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")
        if self.filename:
            str_avail = _("Available")
            str_not_avail = _("Not Available")
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                upload_info = _("<center><h2 style='color:green;'>File is successfully uploaded.</h2></center>")
                temp = self.create_temp_file(self.csv_file)
                index = 1
                upload_info += _(
                    "<table width='80%' align='center' class='table'><thead><tr><th scope='col' width='0%'>No. </th><th scope='col'>Product Code</th><th scope='col'>Product Name</th><th scope='col'>Status</th><th scope='col'>Supplier Available for</th></tr></thead><tbody>")
                try:
                    with open(temp.name, 'r', encoding="ISO-8859-1") as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            print("Index ==> ", index)
                            final_product_code = row[0]
                            if self.prefix_code:
                                final_product_code = self.prefix_code + str(row[0])
                            # supplier_info = self.env["product.supplierinfo"].sudo().search(
                            #     [('product_code', '=', final_product_code if self.supplier_id.id == 83602 else row[0]),
                            #      ('name', '=', self.supplier_id.id)])
                            supplier_info = False
                            self._cr.execute("select id from product_supplierinfo where product_code='%s' and name=%s limit 1" % (final_product_code if self.supplier_id.id == 83602 else row[0],self.supplier_id.id))
                            supplier_result = self._cr.fetchall()
                            if supplier_result:
                                supplier_info = self.env["product.supplierinfo"].browse(supplier_result[0])
                            product_data = supplier_info[0].product_tmpl_id if supplier_info else False
                            if not product_data:
                                #product_data = self.env["product.template"].sudo().search([('default_code', '=', (self.prefix_code + str(row[0])) if self.prefix_code else str(row[0]))],limit=1)
                                self._cr.execute("select id from product_template where default_code='%s' limit 1"%(self.prefix_code + str(row[0])) if self.prefix_code else str(row[0]))
                                result = self._cr.fetchall()
                                if result:
                                    product_data = self.env["product.template"].browse(result[0])
                            if product_data:
                                upload_info += "<tr class='success'><td>" + str(index) + "</td><td>" + str(row[0]) + "</td><td>"+product_data.name+"</td><td>" + str(str_avail) + "</td><td>"+str(list(set([seller.company_id.name for seller in product_data.seller_ids])))+"</td></tr>"
                            else:
                                product_data = self.env["product.template"].sudo().search([('default_code', 'like', (row[0]).strip())], limit=1)
                                if product_data:
                                    upload_info += "<tr class='warning'><td>" + str(index) + "</td><td>" + str(row[0]) + "</td><td></td><td>" + _("Partial available") + "</td><td>"+str([product_data.default_code])+str(product_data.name)+"</td></tr>"
                                else:
                                    upload_info += "<tr class='danger'><td>" + str(index) + "</td><td>" + str(row[0]) + "</td><td></td><td>" + str(str_not_avail) + "</td><td></td></tr>"
                            index += 1
                    upload_info += "</tbody></table>"
                    self.upload_info = upload_info
                except Exception as e:
                    self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")

    def _search_ir_property(self, field_list, new_prod_id):
        for field_name in field_list:
            ir_property = self.env["ir.property"].search([('company_id', '=', self.company_id.id), ('name', '=', field_name.get('field')),('res_id', '=', "%s,%s"%(str(new_prod_id._name,new_prod_id.id)))], limit=1)
            if ir_property:
                ir_property.value_reference = "account.account,"+str(getattr(self, field_name.get('name')).id)
            else:
                new_property_id = self.env["ir.property"].sudo().create({'fields_id':field_name.get('id'),'company_id': self.company_id.id, "name": field_name.get('field'), 'res_id': "%s,%s"%(str(new_prod_id._name,new_prod_id.id)), 'value_reference': "account.account,"+str(getattr(self, field_name.get('name')).id)})

    def _get_property_line(self):
        set_line = []
        for property in self.shopware_property_ids:
            set_line.append((0,0,{'attribute_id':property.attribute_id.id, 'value_ids': [(6,0,property.value_ids.ids)]}))
        return set_line

    def import_sparepart(self):
        if self.filename:
            error_list = []
            is_override = self.need_override
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                temp = self.create_temp_file(self.csv_file)
                try:
                    with open(temp.name, 'r') as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            try:
                                update_vals = {}
                                file_product_code = row[0]
                                final_product_code = row[0]
                                account_list = []
                                if self.prefix_code:
                                    update_vals["default_code"] = self.prefix_code + str(file_product_code)
                                    final_product_code = self.prefix_code + str(file_product_code)
                                if self.price_from_file:
                                    rrp_price = row[2] if row[2] else "0"
                                    rrp_price = rrp_price.replace(",",".")
                                    update_vals["rrp_price"] = float(rrp_price)
                                update_vals["company_id"] = self.company_id.id
                                if self.product_brand_id:
                                    update_vals["product_brand_id"] = self.product_brand_id.id
                                if self.categ_id:
                                    update_vals["categ_id"] = self.categ_id.id
                                if self.property_set_id:
                                    update_vals["property_set_id"] = self.property_set_id.id
                                if self.income_account_id:
                                    account_list.append({"name":"income_account_id","field": "property_account_income_id","id":self.env.ref('account.field_product_template_property_account_income_id').id})
                                if self.expense_account_id:
                                    account_list.append({"name":"expense_account_id","field": "property_account_expense_id", "id": self.env.ref('account.field_product_template_property_account_expense_id').id})
                                if self.price_account_id:
                                    account_list.append({"name":"price_account_id","field": "property_account_creditor_price_difference", "id": self.env.ref('purchase.field_product_template_property_account_creditor_price_difference').id})
                                if self.shopware_categ_ids:
                                    update_vals["shopware_categories"] = [(6, 0, [categ.id for categ in self.shopware_categ_ids])]
                                property_line_data = self._get_property_line()

                                #supplier_info = self.env["product.supplierinfo"].sudo().search([('product_code', '=', final_product_code if self.supplier_id.id == 83602 else file_product_code),('name', '=', self.supplier_id.id)])

                                supplier_info = False
                                self._cr.execute(
                                    "select id from product_supplierinfo where product_code='%s' and name=%s and company_id=%s limit 1" % (
                                    final_product_code if self.supplier_id.id == 83602 else row[0],
                                    self.supplier_id.id, self.company_id.id))
                                supplier_result = self._cr.fetchall()
                                if supplier_result:
                                    supplier_info = self.env["product.supplierinfo"].browse(supplier_result[0])

                                if supplier_info and supplier_info[0].product_id:
                                    new_prod_id = supplier_info[0].product_id
                                else:
                                    new_prod_id = supplier_info[0].product_tmpl_id if supplier_info else False
                                if not new_prod_id:
                                    #new_prod_id = self.env["product.template"].sudo().search([('default_code', '=', (self.prefix_code + str(file_product_code)) if self.prefix_code else str(file_product_code))], limit=1)
                                    self._cr.execute("select id from product_template where default_code='%s' limit 1" % ((self.prefix_code + str(file_product_code)) if self.prefix_code else str(file_product_code)))
                                    result = self._cr.fetchall()
                                    if result:
                                        new_prod_id = self.env["product.template"].browse(result[0])

                                if not new_prod_id:
                                    #new_prod_id = self.env["product.template"].sudo().search([('active', '=', False), ('default_code', '=',(self.prefix_code + str(file_product_code)) if self.prefix_code else str(file_product_code))], limit=1)
                                    self._cr.execute(
                                        "select id from product_template where active='f' and default_code='%s' limit 1" % (
                                            (self.prefix_code + str(file_product_code)) if self.prefix_code else str(
                                                file_product_code)))
                                    result = self._cr.fetchall()
                                    if result:
                                        new_prod_id = self.env["product.template"].browse(result[0])

                                if not new_prod_id:
                                    #new_prod_id = self.env["product.template"].sudo().search([('active', '=', False), ('default_code', '=',(self.prefix_code + str(file_product_code)) if self.prefix_code else str(file_product_code))], limit=1)
                                    self._cr.execute(
                                        "select id from product_product where default_code='%s' limit 1" % (
                                            (self.prefix_code + str(file_product_code)) if self.prefix_code else str(
                                                file_product_code)))
                                    result = self._cr.fetchall()
                                    if result:
                                        new_prod_id = self.env["product.product"].browse(result[0])

                                if new_prod_id:
                                    if is_override:
                                        for field in self.field_map_ids:
                                            if field.name == "taxes_id":
                                                for tax in self.product_id.taxes_id:
                                                    new_prod_id.taxes_id = [(4, tax.id)]
                                            elif field.name == "supplier_taxes_id":
                                                for tax in self.product_id.supplier_taxes_id:
                                                    new_prod_id.supplier_taxes_id = [(4, tax.id)]
                                            else:
                                                setattr(new_prod_id, field.name, getattr(self.product_id, field.name))

                                        supplier_info = False
                                        self._cr.execute(
                                            "select id from product_supplierinfo where product_code='%s' and company_id=%s and (product_tmpl_id=%s or product_id=%s) limit 1" % (
                                                final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                                self.company_id.id,
                                                new_prod_id.id,new_prod_id.id
                                            ))
                                        supplier_result = self._cr.fetchall()
                                        if supplier_result:
                                            supplier_info = self.env["product.supplierinfo"].browse(supplier_result[0])

                                        if supplier_info:
                                            supplier_info.write(
                                                {"product_name": row[1], "product_code": final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                                 "name": self.supplier_id.id,
                                                 "company_id": self.company_id.id})
                                        else:
                                            product_id_data = new_prod_id.id if new_prod_id._name == "product.product" else False
                                            if new_prod_id._name == "product.product":
                                                new_prod_id.variant_seller_ids = [
                                                    (0, 0, {"product_name": row[1],
                                                            "product_code": final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                                            "name": self.supplier_id.id,
                                                            "company_id": self.company_id.id,
                                                            "product_id": new_prod_id.id})]
                                            else:
                                                new_prod_id.seller_ids = [
                                                    (0, 0, {"product_name": row[1], "product_code": final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                                            "name": self.supplier_id.id,
                                                            "company_id": self.company_id.id,
                                                            "product_id": new_prod_id.id if new_prod_id._name == "product.product" else False})]
                                        if self.property_set_id and self.shopware_property_ids:
                                            new_prod_id.shopware_property_ids.unlink()
                                            new_prod_id.shopware_property_ids = property_line_data
                                        if self.name_from_file:
                                            update_vals["name"] = row[1]
                                        self._search_ir_property(account_list, new_prod_id)
                                        #check_prod_id = self.env["product.template"].sudo().search([('default_code', '=',update_vals.get("default_code"))],limit=1)
                                        check_prod_id = False
                                        self._cr.execute("select id from product_template where default_code='%s' limit 1" % (update_vals.get("default_code")))
                                        result = self._cr.fetchall()
                                        if result:
                                            check_prod_id = self.env["product.template"].browse(result[0])
                                        if check_prod_id and check_prod_id.id != new_prod_id.id:
                                            error_list.append("This product code already available so skipped update for %s"%update_vals.get("default_code"))
                                        else:
                                            is_update = new_prod_id.with_context(lang=self.env.user.lang).write(update_vals)
                                        if update_vals.get("name"):
                                            is_update = new_prod_id.with_context(lang='en_US').write({'name':update_vals.get("name")})
                                    else:
                                        continue
                                else:
                                    new_prod_id = self.product_id.with_context(force_company=self.source_company_id.id).copy(default={"default_code":(self.prefix_code + str(file_product_code)) if self.prefix_code else str(row[0])})
                                    for field in self.field_map_ids:
                                        if field.name == "taxes_id":
                                            for tax in self.product_id.taxes_id:
                                                new_prod_id.taxes_id = [(4, tax.id)]
                                        elif field.name == "supplier_taxes_id":
                                            for tax in self.product_id.supplier_taxes_id:
                                                new_prod_id.supplier_taxes_id = [(4, tax.id)]
                                        else:
                                            setattr(new_prod_id, field.name, getattr(self.product_id, field.name))
                                    # supplier_info = self.env["product.supplierinfo"].search(
                                    #     [('product_code', '=', final_product_code if self.supplier_id.id == 83602 else file_product_code), ('company_id', '=', self.company_id.id),
                                    #      ('product_tmpl_id', '=', new_prod_id.id)])
                                    supplier_info = False
                                    self._cr.execute(
                                        "select id from product_supplierinfo where product_code='%s' and company_id=%s and product_tmpl_id=%s limit 1" % (
                                            final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                            self.company_id.id,
                                            new_prod_id.id
                                        ))
                                    supplier_result = self._cr.fetchall()
                                    if supplier_result:
                                        supplier_info = self.env["product.supplierinfo"].browse(supplier_result[0])

                                    if supplier_info:
                                        supplier_info.write(
                                            {"product_name": row[1], "product_code": final_product_code if self.supplier_id.id == 83602 else file_product_code, "name": self.supplier_id.id,
                                             "company_id": self.company_id.id})
                                    else:
                                        new_prod_id.seller_ids = [(0, 0, {"product_name": row[1], "product_code": final_product_code if self.supplier_id.id == 83602 else file_product_code,
                                                                             "name": self.supplier_id.id,
                                                                             "company_id": self.company_id.id})]
                                    update_vals["name"] = row[1]
                                    if self.property_set_id and self.shopware_property_ids:
                                        update_vals["shopware_property_ids"] = property_line_data
                                    check_prod_id = self.env["product.template"].sudo().search([('default_code', '=', update_vals.get("default_code"))], limit=1)
                                    if check_prod_id and check_prod_id.id != new_prod_id.id:
                                        error_list.append("This product code already available so skipped for %s" % update_vals.get("default_code"))
                                    else:
                                        is_update = new_prod_id.with_context(lang=self.env.user.lang).write(update_vals)
                                    if update_vals.get("name"):
                                        is_update = new_prod_id.with_context(lang='en_US').write({'name': update_vals.get("name")})
                                    self._search_ir_property(account_list, new_prod_id)
                                if new_prod_id._name == "product.template":
                                    self._cr.execute("update product_template set company_id=null where id='%s'" % (new_prod_id.id))
                                elif new_prod_id._name == "product.product":
                                    self._cr.execute("update product_template set company_id=null where id='%s'" % (new_prod_id.product_tmpl_id.id))
                            except Exception as e:
                                error_list.append(str(e))
                                continue
                    upload_info = "<center style='color:green;'>Import has been done.</center>"
                    error_list = list(filter(None, error_list))
                    if len(error_list) > 0:
                        upload_info += "<table align='center'><tr><th>Below are the errors</th></tr>"
                        not_found_cat = list(set(error_list))  # Remove duplicate category for print
                        for not_found in not_found_cat:
                            upload_info += "<tr><td>" + not_found + "</td></tr>"
                        upload_info += "</table>"
                    self.upload_info = upload_info
                    return {
                        "type": "ir.actions.do_nothing",
                    }
                except Exception as e:
                    raise UserError(_('Something went wrong, file is not valid or you entered wrong data.\n\n' + str(e)))
            else:
                raise UserError(_('Please upload valid .csv file.'))