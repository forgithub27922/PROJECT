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
from datetime import datetime
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
from odoo.exceptions import UserError
import logging
import requests
import json
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_image_on_server = fields.Boolean(string="Is Image on Image Server?", compute='_is_image_on_imageserver', default=False)

    def _is_image_on_imageserver(self):
        for record in self:
            record.is_image_on_server = False
            try:
                if record.barcode:
                    req=requests.get("https://imageserver.partenics.de/odoo/%s?format=json"%record.barcode)
                    if req.status_code == 200:
                        response = json.loads(req.content.decode("utf-8"))
                        if len(response.get("images",[])) > 0:
                            record.is_image_on_server = True
                        else:
                            record.is_image_on_server = False
            except:
                record.is_image_on_server = False

