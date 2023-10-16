#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
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
from pdf2image import convert_from_path
from brother_ql import BrotherQLRaster, create_label
from brother_ql.backends import backend_factory, guess_backend
from PIL import Image, ImageDraw, ImageFont
import logging


_logger = logging.getLogger(__name__)

class LabelPrinter(models.Model):
    _name = 'label.printer'
    _description = 'Label printer'

    name = fields.Char(string='Printer Name',required=True)
    printer_model = fields.Char(string='Printer Model', required=True)
    printer_location = fields.Char(string='Printer Location', required=True)
    active = fields.Boolean(string="Active")

    def print_label(self, report_name, record_id, rotate=0):
        report_id = self.env['ir.actions.report'].search([('report_name', '=', report_name)], limit=1)
        if not report_id:
            raise Exception("Required report does not exist: ")
        res_data, res_format = report_id.render([record_id])
        temp = tempfile.NamedTemporaryFile()
        temp.write(res_data)
        pages = convert_from_path(temp.name, fmt='PNG')
        selected_backend = guess_backend(self.printer_location)
        BACKEND_CLASS = backend_factory(selected_backend)['backend_class']
        try:
            for page in pages:
                temp = tempfile.NamedTemporaryFile()
                page.save(temp.name, 'PNG')
                im = Image.open(temp.name)
                qlr = BrotherQLRaster(self.printer_model)
                create_label(qlr, im, '62', rotate=rotate)
                be = BACKEND_CLASS(self.printer_location)
                be.write(qlr.data)
                be.dispose()
                temp.close()
            if pages:
                temp.close()
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': _('<b>Printing done successfully..!!</b>'),
                        'type': 'rainbow_man',
                    }
                }
                #self.env.user.notify_info(_('<b>Printing done successfully..!!</b>'))
        except Exception as e:
            temp.close()
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': _('<b>Something is wrong in Label Printer configuration..!!<br/>%s</b>'%str(e)),
                    'type': 'rainbow_man',
                }
            }
            #self.env.user.notify_warning(_('<b>Something is wrong in Label Printer configuration..!!<br/>%s</b>'%str(e)))
        finally:
            temp.close()

class ProductLabelWizard(models.TransientModel):
    _name = "product.label.wizard"
    _description = "Product Label Wizard"


    print_layout = fields.Selection([
        ('s', 'Small'),
        ('b', 'Big')
        ], string='Print Layout', default='s', required=True)
    copy_number = fields.Integer(default=1, string='# of Copies')
    printer_id = fields.Many2one('label.printer', string='Select Printer')

    def print_product_label(self):
         active_model = self._context.get('active_model', False)
         rotation = 0 if self.print_layout == 's' else 90
         if active_model:
            product_ids = self.env[active_model].browse(self._context.get('active_ids', []))
            for product_id in product_ids:
                # label_printer = self.env["label.printer"].search([], limit=1)
                label_printer = self.env["label.printer"].browse(self.printer_id.id)
                if label_printer:
                    for copy_print in range(self.copy_number):
                        prod_id = product_id.id
                        if active_model == "product.template":
                            prod_id = product_id.product_variant_id.id
                        label_printer.print_label('grimm_barcode_scan.product_label_print_template', prod_id,rotate=rotation)
