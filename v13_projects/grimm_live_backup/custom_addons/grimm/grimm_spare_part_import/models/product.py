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

from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def open_assign_variant_wizard(self, active_ids=False):
        if active_ids:
            default_value = {}
            default_value["default_product_id"] = active_ids[0]
            return {
                'type': 'ir.actions.act_window',
                'name': _('Assign Variant Product'),
                'res_model': 'product.merge',
                'view_mode': 'form',
                'target': 'new',
                'context': default_value,
                'views': [[False, 'form']]
            }

    def _create_variant_ids(self):
        '''
        Inherited this method to prevent variant creation during variant assignment.
        :return:
        '''
        if self._context.get("no_variant_create", False):
            return True
        else:
            return super(ProductTemplate, self)._create_variant_ids()

class sparepart_import(models.TransientModel):
    _name = 'sparepart.import'
    _description = 'Sparepart Import'

    product_ids = fields.Many2many(comodel_name='product.template', string='Products')
    which_import = fields.Selection(selection=[('accessory', 'Accessory'), ('part', 'Sparepart')], string='Import', default='part',required=True, help="For sparepart Odoo will check based on supplier and supplier code and for Accessory Odoo will check based on SKU. ")
    csv_file = fields.Binary('Browse File')
    filename = fields.Char('File name')
    download_link = fields.Html('Download Link')
    upload_info = fields.Html("Upload Information")
    device_sparepart_from_file = fields.Boolean("Sparepart / Device from file.", default=False, help="First Column will be Sparepart ID and second column will be device id.")
    supplier_id = fields.Many2one(
        'res.partner',
        string='Part Supplier',
        help="""Select supplier."""
    )
    device_supplier_id = fields.Many2one(
        'res.partner',
        string='Device Supplier',
        help="""Select Device supplier."""
    )

    def create_temp_file(self, csv_data):
        temp = NamedTemporaryFile()
        temp.write(base64.b64decode(csv_data))
        temp.seek(0)
        return temp

    def _compute_rec_link(self, prod_id):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        return '%s/web?db=%s#id=%s&view_type=form&model=product.template' % (base_url, database_name, prod_id)

    @api.onchange('csv_file')
    def filename_change(self):
        prev_attachment = self.env["ir.attachment"].search([('res_model', '=', "sparepart.import")]).unlink()
        self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")
        if self.filename:
            str_avail = _("Available")
            str_not_avail = _("Not Available")
            str_part_avail = _("Partially Available")
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                upload_info = _("<center><h2 style='color:green;'>File is successfully uploaded.</h2><h3>Searched product based on supplier and product code.</h3></center>")
                temp = self.create_temp_file(self.csv_file)
                csv_download = []
                index = 1
                upload_info += _(
                    "<table width='80%' align='center' class='table'><thead><tr><th scope='col' width='20%'>No. </th><th scope='col'>Vendor Code</th><th scope='col'>Status</th></tr></thead><tbody>")
                csv_download.append([_('No.'), _('Vendor Code'), _('Status')])
                try:
                    with open(temp.name, 'r', encoding="ISO-8859-1") as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            product_data = self._serach_product_code(row[0], self.supplier_id.id)
                            if product_data:
                                upload_info += "<tr><td>" + str(index) + "</td><td>" + str(
                                    (row[0]).strip()) + "</td><td style='color:green;'>" + str_avail + "</td></tr>"
                                csv_download.append([index, str(row[0]).strip(), str_avail])
                            else:
                                product_data = self.env["product.supplierinfo"].search(
                                    [('product_code', 'like', (row[0]).strip()), ('name', '=', self.supplier_id.id)], limit=1)
                                if product_data:
                                    upload_info += "<tr><td>" + str(index) + "</td><td>" + str((row[
                                        0]).strip()) + "</td><td style='color:blue;'>" + str_part_avail + " in <a target='blank' href='"+self._compute_rec_link(product_data.product_tmpl_id.id)+"'>"+str([product_data.product_tmpl_id.default_code])+ product_data.product_tmpl_id.name+"</a></td></tr>"
                                    csv_download.append([index, str(row[0]).strip(), str_part_avail + " in " +str([product_data.product_tmpl_id.default_code])+ product_data.product_tmpl_id.name])
                                else:
                                    upload_info += "<tr><td>" + str(index) + "</td><td>" + str((row[
                                        0]).strip()) + "</td><td style='color:red;'>" + str_not_avail + "</td></tr>"
                                    csv_download.append([index, str(row[0]).strip(), str_not_avail])
                            index += 1
                    upload_info += "</tbody></table>"

                    download_file = NamedTemporaryFile()
                    with open(download_file.name, mode='w') as download:
                        download_writer = csv.writer(download, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        for csv_data in csv_download:
                            download_writer.writerow(csv_data)
                    data = open(download_file.name, "rb").read()
                    encoded = base64.b64encode(data)
                    attach_id = self.env["ir.attachment"].create(
                        {"name": "Temp File for sparepart import",
                         "datas": encoded,
                         "public": True,
                         "res_model": "sparepart.import",
                         "datas_fname": "sparepart_result.csv"})
                    self.download_link = "<a href='/web/content/" + str(
                        attach_id.id) + "/download_result.csv'>Download Result</a>"
                    self.upload_info = upload_info
                except Exception as e:
                    self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.csv_file = False
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")

    def _serach_product_code(self, sup_code, sup_id):
        product_data = self.env["product.supplierinfo"].search([('product_code', '=', (sup_code).strip()), ('name', '=', sup_id)], limit=1)
        if product_data:
            return product_data.product_tmpl_id if product_data.product_tmpl_id else False
        else:
            False

    def import_sparepart(self):
        if self.filename:
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                temp = self.create_temp_file(self.csv_file)
                csv_products = []
                try:
                    with open(temp.name, 'r', encoding="ISO-8859-1") as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            if self.which_import == 'part':
                                product_data = self._serach_product_code(row[0], self.supplier_id.id)
                                if self.device_sparepart_from_file:
                                    device_product_data = self._serach_product_code(row[1], self.device_supplier_id.id if self.device_supplier_id else self.supplier_id.id)
                                    if product_data and device_product_data:
                                        existed_spare_part = device_product_data.spare_part_prod_ids.filtered(lambda rec: rec.spare_part_id.id == device_product_data.id)
                                        if not existed_spare_part:
                                            device_product_data.spare_part_prod_ids = [(0, 0, {"spare_part_id": product_data.id, "position": 0})]
                                else:
                                    if product_data:
                                        csv_products.append(product_data.id)
                            else:
                                main_product_data = self.env["product.template"].search([('default_code', '=', (row[0]).strip())], limit=1)
                                accessory_product_data = self.env["product.template"].search([('default_code', '=', (row[1]).strip())], limit=1)
                                position = 0
                                try:
                                    position = row[2]
                                except IndexError:
                                    position = 0
                                if main_product_data and accessory_product_data:
                                    existed_accessory = main_product_data.accessory_part_ids.filtered(lambda rec: rec.accessory_part_id.id == accessory_product_data.id)
                                    for existed_acc in existed_accessory:
                                        existed_acc.position=position
                                    if not existed_accessory:
                                        main_product_data.accessory_part_ids = [(0, 0, {"accessory_part_id":accessory_product_data.id, "position": position})]
                    for prod in csv_products:
                        for base_prod in self.product_ids:
                            base_prod.spare_part_prod_ids = [(0, 0, {"spare_part_id": prod, "position": 0})]
                except Exception as e:
                    self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
