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
from email.utils import formataddr

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def default_get(self, fields_list):
        defaults = super(HolidaysRequest, self).default_get(fields_list)
        if self._context.get("default_holiday_status_id", False):
            defaults['holiday_status_id'] = self._context.get('default_holiday_status_id')
        return defaults

    def unlink(self):
        validation_type = self.mapped('holiday_status_id.validation_type')
        if len(validation_type) == 1 and "no_validation" in validation_type:
            for holiday in self:
                if holiday.holiday_status_id.validation_type == "no_validation":
                    self._cr.execute("delete from hr_leave where id=%s" % (holiday.id))
            return True
        return super(HolidaysRequest, self).unlink()