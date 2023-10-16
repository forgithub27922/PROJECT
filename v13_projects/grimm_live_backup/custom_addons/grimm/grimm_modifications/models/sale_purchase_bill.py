#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dipaksuthar.gvp@gmail.com>
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
from odoo import models, fields, api
from odoo.tools.misc import formatLang, get_lang
import re
import logging
_logger = logging.getLogger(__name__)

class SalePurchaseBill(models.Model):
    _inherit = 'purchase.order.line'

    line_no = fields.Char('APos.', help="Positionsnummer aus Verkaufsauftrag")
    vendor_code = fields.Char(string="Vendor code",compute='_compute_vendor_code',readonly=True)

    def _prepare_account_move_line(self, move):
        res = super(SalePurchaseBill, self)._prepare_account_move_line(move)
        res["line_no_stored"] = self.line_no or ""
        return res


    def _compute_vendor_code(self):
        for record in self:
            product_lang = record.product_id.with_context(
                lang=get_lang(self.env, self.partner_id.lang).code,
                partner_id=self.partner_id.id,
                company_id=self.company_id.id,
            )
            full_name = record._get_product_purchase_description(product_lang)
            pattern = "\[(.*?)\]"
            try:
                record.vendor_code = re.search(pattern, full_name).group(1)
                record.name = record.name.replace(re.search(pattern, full_name).group(), "")
            except:
                record.vendor_code = ""


    @api.model
    def create(self, vals):
        # {'product_qty': 2.0, 'product_uom': 1, 'date_planned': '2020-02-11 13:55:16', 'taxes_id': [(6, 0, [14])], 'price_unit': 68.11, 'order_id': 32400, 'orderpoint_id': False, 'sale_line_id': 148961, 'product_id': 600698, 'name': '[32261303] Lenkstoprolle CNS 160', 'move_dest_ids': []}
        # {'product_qty': 2.0, 'product_uom': 1, 'date_planned': '2020-02-11 13:55:16', 'taxes_id': [(6, 0, [14])], 'price_unit': 45.5, 'order_id': 32400, 'orderpoint_id': False, 'sale_line_id': 148962, 'product_id': 600699, 'name': '[32262303] Bockrolle CNS 160', 'move_dest_ids': []}
        # Added sequence to purchase order line when it's created from SO
        if 'sale_line_id' in vals:
            sol = self.env['sale.order.line'].browse(vals.get('sale_line_id'))
            vals.update({'line_no': sol.line_no})

        return super(SalePurchaseBill, self).create(vals)


class VendorBill(models.Model):
    _inherit = 'account.move.line'

    line_no_stored = fields.Char(string='APos', help="Positionsnummer aus Verkaufsauftrag")

    @api.model
    def create(self, vals):
        vals.update({'line_no_stored': vals.get('line_no', '')})
        purchase_line_id = vals.get("purchase_line_id", False)
        if purchase_line_id:
            purchase_line = self.env["purchase.order.line"].browse(purchase_line_id)
            if purchase_line and purchase_line.line_no:
                vals.update({'line_no_stored': purchase_line.line_no})
        return super(VendorBill, self).create(vals)
