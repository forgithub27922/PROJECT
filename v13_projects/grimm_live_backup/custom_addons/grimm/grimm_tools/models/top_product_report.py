#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
import tempfile
from tempfile import NamedTemporaryFile
from pdf2image import convert_from_path
from brother_ql import BrotherQLRaster, create_label
from brother_ql.backends import backend_factory, guess_backend
import csv
import ast
import base64
import logging


_logger = logging.getLogger(__name__)

class TopProductReport(models.Model):
    _name = 'top.product.report'
    _description = 'Top Product Report'

    name = fields.Char(string='Name',required=True, default="Product Export")
    model_domain = fields.Char(string='Domain')
    csv_file = fields.Binary('Browse File', attachment=True)
    filename = fields.Char('File name')
    download_link = fields.Html('Download Link')
    record_limit = fields.Integer('Limit', default=100)
    order_by = fields.Char('Order by')

    def create_temp_file(self, csv_data):
        temp = NamedTemporaryFile()
        temp.write(base64.b64decode(csv_data))
        temp.seek(0)
        return temp

    def export_products(self):
        download_file = NamedTemporaryFile()

        domain = ast.literal_eval(self.model_domain or '[]')
        product_product = self.env['product.product'].sudo().search(domain, limit=self.record_limit or None, order=self.order_by or 'id')

        with open(download_file.name, mode='w') as download:
            download_writer = csv.writer(download, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            download_writer.writerow(["SKU", "Name", "#Sales", "Purchase Price", "Sale Price", "Margin(%)"])
            for product in product_product:#csv_download:
                purchase_price = product.calculated_standard_price
                sale_price = product.calculated_magento_price
                difference = (abs(purchase_price - sale_price) / sale_price) * 100.0
                val_list = [
                    product.default_code,
                    product.name,
                    product.sales_count,
                    purchase_price,
                    sale_price,
                    difference
                ]
                download_writer.writerow(val_list)
        data = open(download_file.name, "rb").read()
        encoded = base64.b64encode(data)
        attach_id = self.env["ir.attachment"].create(
            {"name": "Temp File for sparepart import",
             "datas": encoded,
             "public": True,
             "res_model": "product.import.convert",
             "datas_fname": "sparepart_result.csv"})
        self.download_link = "<a href='/web/content/" + str(attach_id.id) + "/converted_result.csv'>Download Converted file</a>"
        print("===================My download link is ====> ", self.download_link)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'top.product.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
