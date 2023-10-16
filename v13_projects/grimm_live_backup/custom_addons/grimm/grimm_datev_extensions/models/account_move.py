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
import odoo
import smtplib
import base64
import psycopg2

from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import math
from tempfile import TemporaryFile, NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv
from datetime import datetime
from datetime import timedelta
import re
import tempfile
from email.utils import formataddr

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_grimm_xml(self):
        data = {}
        if len(self) == 1:
            return self._export_as_facturx_xml()
        else:
            for move in self:
                data[str(move.id)] = move._export_as_facturx_xml()
        return data

    def invoice_edi_export(self):
        active_id = self.env.context.get('active_ids', False)
        if len(active_id) == 1:
            invoice = self.browse(active_id)
            datas = base64.b64encode(invoice.get_grimm_xml())
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')

            self._cr.execute("select id from ir_attachment where res_id=-999 and res_model='account.move';")
            need_to_delete = [x[0] for x in self._cr.fetchall()]
            self.env['ir.attachment'].browse(need_to_delete).unlink() # Deleting old record of ir attachment

            attachment_id = self.env['ir.attachment'].create({'name': "%s.xml"%invoice.name, 'datas_fname': '%s.xml'%invoice.name, 'datas': datas, "res_model":"account.move", "res_id":-999})
            download_url = "%s/web/content/%s?download=true"%(base_url,attachment_id.id)
            return {
                "type": "ir.actions.act_url",
                "url": "%s"%(download_url),
                "target": "new",
            }