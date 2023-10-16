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
from odoo.tools import float_compare, pycompat
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import ValidationError
import uuid


class CRMClaim(models.Model):
    _inherit = "crm.claim"

    ticket_id = fields.Many2one("helpdesk.ticket",string="Helpdesk Ticket")
    public_id = fields.Char(string="Public ID", default=lambda self: "%s-%s"%(uuid.uuid4().hex,uuid.uuid4().hex))
    manufacturer_id = fields.Many2one("grimm.product.brand", string="Manufacturer ID")
    serial_number = fields.Char("Serien-Nr")
    lieferdatum = fields.Date("Lieferdatum")
    device_description = fields.Char("Gerätebezeichnung")
    partner_parent_id = fields.Many2one("res.partner", compute="_get_main_parent")
    inv_id = fields.Many2one("account.move", string="Rechnung ID")

    @api.depends('partner_id')
    def _get_main_parent(self):
        self.partner_parent_id = False
        for this in self:
            if this.partner_id:
                parent_partner = this.partner_id
                while parent_partner.parent_id:
                    parent_partner = parent_partner.parent_id
                this.partner_parent_id = parent_partner

