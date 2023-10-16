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

class PartnerAgedFilter(models.Model):
    _name = 'partner.aged.filter'
    _description = 'Partner Aged Filter'
    _order = 'name'

    name = fields.Char(string='Filter',required=True)
    active = fields.Boolean(string='Active')
    duration = fields.Integer(string='Duration', default=30, required=True)