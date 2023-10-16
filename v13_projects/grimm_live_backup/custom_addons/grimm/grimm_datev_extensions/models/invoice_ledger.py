#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 Grimm Gastrobedarf
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
import logging
import os
import csv
import zipfile
import base64
from tempfile import NamedTemporaryFile
import tempfile


_logger = logging.getLogger(__name__)

class InvoiceLedgerExport(models.Model):
    _name = 'invoice.ledger.export'
    _description = 'Invoice Ledger Export'
    _order = 'write_date desc'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    include_fibu = fields.Boolean("Include Fibu", default=False)
    include_approved = fields.Boolean("Include Approved", default=True)
    zip_file = fields.Binary('.Zip File', attachment=True)
    file_name = fields.Char("Final Name")
    invoice_ids = fields.Many2many(comodel_name='x_incoming_invoice', string='Invoices', readonly=True)
    inv_csv_file = fields.Binary(string='.csv File', readonly=True,
                                 help="CSV file contains all invoices ids which exported in this export.",
                                 attachment=True)
    inv_csv_filename = fields.Char(string='CSV Filename', readonly=True, default=lambda *a: 'invoices.csv')

    def create_temp_file(self, data, dir=tempfile.gettempdir()):
        temp = NamedTemporaryFile(dir=dir, delete=False)
        temp.write(base64.b64decode(data))
        temp.seek(0)
        temp.close()
        return temp

    def reset_export(self):
        self.ensure_one()
        self.invoice_ids.write({'x_studio_field_YXFiF':False})

    def zepdir(self, path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                ziph.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(path, '..')))


    def create_zip_file(self, dir_name):
        temp_zip = NamedTemporaryFile(delete=False)
        self.file_name = "%s_To_%s_%s.zip" % (self.start_date, self.end_date,fields.Datetime.now())
        self.inv_csv_filename = "%s_To_%s_%s.csv" % (self.start_date, self.end_date, fields.Datetime.now())
        temp_zip.name = self.file_name
        zf = zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED)
        self.zepdir(dir_name, zf)
        zf.close()
        return temp_zip


    def get_file(self):
        form_view_id = self.env.ref('grimm_datev_extensions.invoice_ledger_export_wizard').id
        total_invoices = self.env['x_incoming_invoice'].sudo().search([('x_studio_field_GR4aX', '>=', self.start_date),('x_studio_field_GR4aX', '<=', self.end_date)])
        invoice_fields = [k for k, v in total_invoices._fields.items()]
        if 'x_studio_field_d5YRb' in invoice_fields: # Created new field on prod via Odoo Studio, so wanted to avoid exception. x_studio_field_d5YRb
            total_invoices = total_invoices.filtered(lambda rec: not rec.x_studio_field_d5YRb)
        if self.include_fibu:
            total_invoices = total_invoices.filtered(lambda rec: rec.x_studio_field_YXFiF in [True, False])
        else:
            total_invoices = total_invoices.filtered(lambda rec: rec.x_studio_field_YXFiF in [False])

        if self.include_approved:
            total_invoices = total_invoices.filtered(lambda rec: rec.x_studio_field_Pd8eI in [True])
        else:
            total_invoices = total_invoices.filtered(lambda rec: rec.x_studio_field_Pd8eI in [False])
        attachments = self.env['ir.attachment'].sudo().search([('res_id', 'in', total_invoices.ids),('res_model', '=', 'x_incoming_invoice')])

        tmpdir = os.path.join(tempfile.gettempdir(), "%s_To_%s_%s" % (self.start_date, self.end_date,fields.Datetime.now()))
        os.makedirs(tmpdir)

        for attachment in attachments:
            if attachment.datas:
                file_data = self.create_temp_file(attachment.datas, dir=tmpdir)
                os.rename(file_data.name, "%s/RE-%s.pdf"%(tmpdir,attachment.res_id))

        temp_zip_file = self.create_zip_file(tmpdir)
        data_zip = open(temp_zip_file.name, "rb").read()
        encoded_zip = base64.b64encode(data_zip)
        self.zip_file = encoded_zip
        total_invoices.x_studio_field_YXFiF = True
        self.invoice_ids = [(6,0,total_invoices._ids)]

        csv_file = NamedTemporaryFile()
        with open(csv_file.name, mode='w') as download:
            download_writer = csv.writer(download, delimiter=';')
            download_writer.writerow(['ID', 'Invoice Number', 'Invoice Date', 'Approved By'])
            for inv_id in total_invoices:
                download_writer.writerow([inv_id.id, inv_id.x_studio_field_yiw0F,inv_id.x_studio_field_GR4aX,inv_id.x_studio_field_DgZio.name])

        csv_data = open(csv_file.name, "rb").read()
        csv_encoded = base64.b64encode(csv_data)
        self.inv_csv_file = csv_encoded


        self.env.cr.commit()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.ledger.export',
            'views': [(form_view_id, 'form')],
            'res_id': self._origin.id,
            'context': {'create': False},
            'name': 'Export Invoice',
            'target': 'new',
        }


