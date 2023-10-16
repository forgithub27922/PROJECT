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
from datetime import datetime, timedelta
from tempfile import TemporaryFile, NamedTemporaryFile
import csv
import time
import base64
import logging

_logger = logging.getLogger(__name__)

class DatevExportHistory(models.Model):
    _name = "datev.export.history"
    _description = "DATEV Export History"

    _order = 'write_date desc'

    in_invoice = fields.Boolean(string='Incoming Invoices', default=lambda *a: True, readonly=True)
    out_invoice = fields.Boolean(string='Outgoing Invoices', default=lambda *a: True, readonly=True)
    in_refund = fields.Boolean(string='Incoming Refunds', default=lambda *a: True, readonly=True)
    out_refund = fields.Boolean(string='Outgoing Refunds', default=lambda *a: True, readonly=True)
    date_start = fields.Date(string='From Date', help="Ignored if Period is selected", readonly=True)
    date_stop = fields.Date(string='To Date', help="Ignored if Period is selected", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required = True, default=lambda self: self.env['res.users'].browse(self._uid).company_id.id, readonly=True)
    datev_file = fields.Binary(string='.zip File', readonly = True, attachment=True)
    datev_filename = fields.Char(string='Filename', size=64, readonly=True, default=lambda *a: 'xml.zip')
    response_message = fields.Text(string='Response Message', readonly=True)
    write_date = fields.Datetime('Exported Datetime', readonly=True)
    export_uid = fields.Many2one('res.users', 'Exported by', readonly=True)
    invoice_ids = fields.Many2many(comodel_name='account.move', string='Invoices', readonly=True)
    inv_csv_file = fields.Binary(string='.csv File', readonly=True, help="CSV file contains all invoices ids which exported in this export.", attachment=True)
    inv_csv_filename = fields.Char(string='CSV Filename', size=64, readonly=True, default=lambda *a: 'invoices.csv')

    def reset_export(self):
        self.ensure_one()
        self.invoice_ids.write({'exported_to_datev':False})


    @api.model
    def _remove_datev_history(self):
        '''
        This method will be called from cron job.
        :return:
        '''
        company_ids = self.env['res.company'].sudo().search([])
        for company_id in company_ids:
            if company_id.history_days > 0:
                domain_date = datetime.now() - timedelta(company_id.history_days) # Get domain date based on configuration
                history_ids = self.env['datev.export.history'].sudo().search([('write_date', '<=', str(domain_date)),('company_id', '=', company_id.id)])
                history_ids.sudo().unlink()
                datev_export = self.env['datev.export.options'].sudo().search([('write_date', '<=', str(domain_date)),('company_id', '=', company_id.id)])
                datev_export.sudo().unlink() # Also removed data from base Transient Model

    def send_datev_export_email(self):
        template = self.env.ref('grimm_datev_extensions.datev_export_email_template', raise_if_not_found=False)
        if template:
            attachment = {
                'name': str(self.datev_filename),
                'datas': self.datev_file,
                'datas_fname': self.datev_filename,
                'res_model': 'datev.export.history',
                'type': 'binary'
            }
            ir_id = self.env['ir.attachment'].sudo().create(attachment)
            datev_history_emails = self.env["ir.config_parameter"].sudo().get_param("datev.history.emails", default=False)
            if datev_history_emails:
                template.email_to = datev_history_emails
            template.attachment_ids = [(4, ir_id.id)] #Added attachment to email template.
            template.sudo().send_mail(self.id, raise_exception=False, force_send=True)
            template.attachment_ids = [(3, ir_id.id)] #Removed attachment to email template.


class DatevExport(models.TransientModel):
    """ DATEV export inherit to override create method """
    _inherit = "datev.export"

    def write(self, vals):
        base_vals = vals.copy()
        del base_vals["invoice_ids"]
        res=  super(DatevExport, self).write(base_vals)
        for data in self:
            if vals.get('filename', False) and vals.get('file', False):
                if vals.get('invoice_ids', False):
                    invoice_ids = self.env['account.move'].browse(vals.get('invoice_ids', []))
                    download_file = NamedTemporaryFile()
                    with open(download_file.name, mode='w') as download:
                        download_writer = csv.writer(download, delimiter=';')
                        download_writer.writerow(['ID', 'Invoice Number'])
                        for inv_id in invoice_ids:
                            if inv_id.state in ('open', 'posted'):
                                download_writer.writerow([inv_id.id, inv_id.name])
                    csv_data = open(download_file.name, "rb").read()
                    encoded = base64.b64encode(csv_data)
                    vals.update({'inv_csv_filename': time.strftime('%Y_%m_%d_%H_%M')+'_invoices.csv', 'inv_csv_file':encoded,'invoice_ids':[(6, 0, invoice_ids._ids)]})

                vals.update(
                    {
                        'datev_filename': "Manually_selected_"+vals.get('filename', "xml.zip"),
                        'datev_file': vals.get('file', False),
                        'out_invoice': False,
                        'in_invoice': False,
                        'in_refund': False,
                        'out_refund': False,
                        'export_uid': data.write_uid.id,
                     }
                )
                history_id = self.env['datev.export.history'].sudo().create(vals)
                if history_id.company_id.datev_send_email:
                    history_id.send_datev_export_email()
        return res

class DatevExportOptions(models.TransientModel):
    """ DATEV export inherit to override create method """
    _inherit = "datev.export.options"

    def write(self, vals):
        base_vals = vals.copy()
        if base_vals.get("invoice_ids", False):
            del base_vals["invoice_ids"]
        res=  super(DatevExportOptions, self).write(base_vals)
        for data in self:
            if vals.get('datev_filename', False) and vals.get('datev_file', False):
                if vals.get('invoice_ids', False):

                    download_file = NamedTemporaryFile()
                    with open(download_file.name, mode='w') as download:
                        download_writer = csv.writer(download, delimiter=';')
                        download_writer.writerow(['ID', 'Invoice Number'])
                        for inv_id in vals.get('invoice_ids', False):
                            if inv_id.state in ('open','posted'):
                                download_writer.writerow([inv_id.id, inv_id.name])
                    csv_data = open(download_file.name, "rb").read()
                    encoded = base64.b64encode(csv_data)
                    vals.update({'inv_csv_filename': time.strftime('%Y_%m_%d_%H_%M')+'_invoices.csv', 'inv_csv_file':encoded,'invoice_ids':[(6, 0, vals.get('invoice_ids', False)._ids)]})

                vals.update(
                    {
                        'in_invoice': data.in_invoice,
                        'out_invoice': data.out_invoice,
                        'in_refund': data.in_refund,
                        'out_refund': data.out_refund,
                        'date_start': data.date_start,
                        'date_stop': data.date_stop,
                        'export_uid': data.write_uid.id,
                     }
                )
                del vals["state"]
                history_id = self.env['datev.export.history'].sudo().create(vals)
                if history_id.company_id.datev_send_email:
                    history_id.send_datev_export_email()

        return res