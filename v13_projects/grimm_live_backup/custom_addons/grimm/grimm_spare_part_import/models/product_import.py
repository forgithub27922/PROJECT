# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dipak Suthar
#    Copyright 2020 Grimm Gastrobedarf
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
import uuid
import base64
from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv
_logger = logging.getLogger(__name__)


class product_import_convert(models.TransientModel):
    _name = 'product.import.convert'
    _description = 'Product Import Convert'

    operation_type = fields.Selection(selection=[('convert', 'Convert File'), ('import', 'Import Property')], string='Operation Type',
                                    default='convert', required=True,
                                    help="1. Convert File :- Using this features you can convert odoo import compatible file. <br/>2. Import Property :- You can update property set, property attribute and shopware categories.")
    csv_file = fields.Binary('Browse File')
    filename = fields.Char('File name')
    download_link = fields.Html('Download Link')
    upload_info = fields.Html("Upload Information")

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
        prev_attachment = self.env["ir.attachment"].search([('res_model', '=', "product.import.convert")]).unlink()
        self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")
        if self.filename:
            str_avail = _("Available")
            str_not_avail = _("Not Available")
            str_part_avail = _("Partially Available")
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                upload_info = _("<center><h2 style='color:green;'>File is successfully uploaded.</h2></center>")
                temp = self.create_temp_file(self.csv_file)
                csv_download = []
                try:
                    if self.operation_type == 'convert':
                        with open(temp.name, 'r', encoding="UTF-8") as inp:
                            header = next(inp, None).split(";")
                            header = [x.lower() for x in header]
                            prod_id_index = header.index("id")
                            categ_id_index = header.index("categ_id/id") if "categ_id/id" in header else -1
                            attribute_id_index = header.index("attribute_set_id/id") if "attribute_set_id/id" in header else -1
                            brand_id_index = header.index("product_brand_id/id") if "product_brand_id/id" in header else -1
                            csv_download.append(header)
                            for row in csv.reader(inp, delimiter=';'):
                                if prod_id_index >= 0:
                                    product_xml_data = self._serach_xml_id(row[prod_id_index],'product.template')
                                    if product_xml_data:
                                        row[prod_id_index] = product_xml_data
                                    else:
                                        continue
                                if categ_id_index >= 0:
                                    category_xml_data = self._serach_xml_id_by_name(row[categ_id_index],'product.category', compare_field = 'complete_name')
                                    print
                                    if category_xml_data:
                                        row[categ_id_index] = category_xml_data
                                    else:
                                        row[categ_id_index] = ""
                                if attribute_id_index >= 0:
                                    attribute_xml_data = self._serach_xml_id_by_name(row[attribute_id_index],'product.attribute.set')
                                    if attribute_xml_data:
                                        row[attribute_id_index] = attribute_xml_data
                                    else:
                                        row[attribute_id_index] = ""
                                if brand_id_index >= 0:
                                    brand_xml_data = self._serach_xml_id_by_name(row[brand_id_index],'grimm.product.brand')
                                    if brand_xml_data:
                                        row[brand_id_index] = brand_xml_data
                                    else:
                                        row[brand_id_index] = ""
                                csv_download.append(row)
                        upload_info += "</tbody></table>"

                        download_file = NamedTemporaryFile()
                        with open(download_file.name, mode='w') as download:
                            download_writer = csv.writer(download, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                            for csv_data in csv_download:
                                download_writer.writerow(csv_data)
                        data = open(download_file.name, "rb").read()
                        encoded = base64.b64encode(data)
                        attach_id = self.env["ir.attachment"].create(
                            {"name": "Temp File for sparepart import",
                             "datas": encoded,
                             "public": True,
                             "res_model": "product.import.convert",
                             "datas_fname": "sparepart_result.csv"})
                        self.download_link = "<a href='/web/content/" + str(
                            attach_id.id) + "/converted_result.csv'>Download Converted file</a>"
                    self.upload_info = upload_info
                except Exception as e:
                    self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.csv_file = False
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload .csv file.</h2></center>")

    def _serach_xml_id(self, res_id, model_name):
        record_obj = self.env[model_name].browse([res_id])
        if record_obj:
            metadata = record_obj.sudo().get_metadata()
            if metadata:
                return_res = metadata[0].get("xmlid") if metadata else False
                if not return_res:
                    return self._create_xml_id(res_id,model_name)
                else:
                    return return_res
        return False

    def _create_xml_id(self, res_id, model_name):
        record_obj = self.env[model_name].browse([res_id])
        ir_name = "%s_%s_%s"%(record_obj._table,record_obj.id,uuid.uuid4().hex[:8])
        create_xml = self.env["ir.model.data"].sudo().create({'name':ir_name, 'module':'__export__', 'res_id':record_obj.id,'model':model_name})
        return "__export__.%s"%ir_name

    def _serach_xml_id_by_name(self, res_name, model_name, compare_field='name', partenics_categ = False):
        res_data = False
        if model_name == 'product.category' and partenics_categ:
            resource = self.env[model_name].search([(compare_field, '=', res_name)])
            for res in resource:
                categ = res.parent_id
                while categ:
                    if not categ.parent_id:
                        break
                    categ = categ.parent_id
                if categ.id == 969: #added partenics category id to check parent category
                    res_data = res
                    break
        else:
            res_data = self.env[model_name].search([(compare_field, '=', res_name)], limit=1)
        if res_data:
            xml_id = self._serach_xml_id(res_data.id, model_name)
            return xml_id if xml_id else False
        return False

    def import_file(self):
        if self.filename:
            extension = os.path.splitext(self.filename)[1]
            not_found_cat = []
            if extension.lower() == ".csv":
                temp = self.create_temp_file(self.csv_file)
                try:
                    with open(temp.name, 'r', encoding="UTF-8") as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            product_id = self.env.ref(row[0].strip(), False) if row[0] else False
                            if product_id:

                                first_cat = self._serach_xml_id_by_name(row[1].strip(),'product.category', partenics_categ = True) if 1 < len(row) else False
                                second_cat = self._serach_xml_id_by_name(row[2].strip(), 'product.category', partenics_categ = True) if 2 < len(row) else False
                                third_cat = self._serach_xml_id_by_name(row[3].strip(), 'product.category', partenics_categ = True) if 3 < len(row) else False
                                categ1 = self.env.ref(first_cat) if first_cat else False
                                categ2 = self.env.ref(second_cat) if second_cat else False
                                categ3 = self.env.ref(third_cat) if third_cat else False
                                property_id = self._serach_xml_id_by_name(row[1].strip(),'property.set') if 1 < len(row) else False
                                property_set_id = self.env.ref(property_id) if property_id else False
                                if not categ1:
                                    not_found_cat.append(row[1].strip() if 1 < len(row) else False)

                                if categ2:
                                    product_id.shopware_categories = [(4, categ2.id)]
                                else:
                                    not_found_cat.append(row[2].strip() if 2 < len(row) else False)

                                if categ3:
                                    product_id.shopware_categories = [(4, categ3.id)]
                                else:
                                    not_found_cat.append(row[3].strip() if 3 < len(row) else False)

                                if not categ2 and not categ3 and categ1:
                                    product_id.shopware_categories = [(4, categ1.id)]
                                if property_set_id:
                                    product_id.property_set_id = property_set_id.id

                                ersatzteil_attr_id = self.env.ref("__export__.product_attribute_636_c78115ae", False) #Reference of Ersatzteilkategorie attribute
                                if not ersatzteil_attr_id:
                                    ersatzteil_attr_id = self.env["product.attribute"].search([('name', '=', 'Ersatzteilkategorie')], limit=1)
                                    assert ersatzteil_attr_id

                                ersatzteil_group_attr_id = self.env.ref("__export__.product_attribute_652_c19b104f", False) #Reference of Ersatzteilgruppen attribute
                                if not ersatzteil_group_attr_id:
                                    ersatzteil_group_attr_id = self.env["product.attribute"].search([('name', '=', 'Ersatzteilgruppen')], limit=1)
                                    assert ersatzteil_group_attr_id
                                add_ersatzteil_categ_id = True
                                add_ersatzteil_group_id = True
                                for property_id in product_id.shopware_property_ids:
                                    if property_id.attribute_id.id == ersatzteil_attr_id.id:
                                        add_ersatzteil_categ_id = False
                                    if property_id.attribute_id.id == ersatzteil_group_attr_id.id:
                                        add_ersatzteil_group_id = False
                                if 4 < len(row) and row[4].strip() and add_ersatzteil_categ_id:
                                    ersatzteil_categ_id = self.env["product.attribute.value"].search([('attribute_id', '=', ersatzteil_attr_id.id),('name', '=', row[4].strip())], limit=1)
                                    if not ersatzteil_categ_id:
                                        ersatzteil_categ_id = self.env["product.attribute.value"].create({'attribute_id':ersatzteil_attr_id.id, 'name': row[4].strip()})
                                    if ersatzteil_categ_id:
                                        product_id.shopware_property_ids = [(0, 0, {"attribute_id": ersatzteil_attr_id.id, 'value_ids': [(4, ersatzteil_categ_id.id)]})]
                                if 5 < len(row) and row[5].strip() and add_ersatzteil_group_id:
                                    ersatzteil_group_id = self.env["product.attribute.value"].search([('attribute_id', '=', ersatzteil_group_attr_id.id), ('name', '=', row[5].strip())], limit=1)
                                    if not ersatzteil_group_id:
                                        ersatzteil_group_id = self.env["product.attribute.value"].create({'attribute_id': ersatzteil_group_attr_id.id, 'name': row[5].strip()})
                                    if ersatzteil_group_id:
                                        product_id.shopware_property_ids = [(0,0, {"attribute_id":ersatzteil_group_attr_id.id, 'value_ids': [(4, ersatzteil_group_id.id)]})]
                except Exception as e:
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
            upload_info = "<center style='color:green;'>Import has been done.</center>"
            not_found_cat = list(filter(None, not_found_cat))
            if len(not_found_cat) > 0:
                upload_info += "<table align='center'><tr><th>Not found Category</th></tr>"
                not_found_cat = list(set(not_found_cat)) # Remove duplicate category for print
                for not_found in not_found_cat:
                    upload_info += "<tr><td>"+not_found+"</td></tr>"
                upload_info += "</table>"
            self.upload_info = upload_info
        return {
            "type": "ir.actions.do_nothing",
        }