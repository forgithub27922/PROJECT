#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Author :- Dipak Suthar
#
#  Copyright 2017 Dipak Suthar <dhbahr@gmail.com>
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

_logger = logging.getLogger(__name__)

class Postalcode(models.Model):
    _name = 'postalcode'
    _description = 'Postalcode'
    name = fields.Char(string='Name', required=True)

    _sql_constraints = [
        ('postalcode_uniq', 'unique(name)',
         "Postalcode with the same name already exists.")
    ]

class ProductPostalcode(models.Model):
    _name = 'product.postalcode'
    _description = 'Product postalcode'

    name = fields.Char(string='Name',required=True)
    active = fields.Boolean(string='Active')
    action_by = fields.Selection(
        [('product', 'By Product'), ('categ', 'By Product Category')],
        string='Action By', default='product', required=True)
    product_ids = fields.Many2many('product.product', string='Products')
    postalcode_ids = fields.Many2many('postalcode', string='Postalcodes')
    product_categ_id = fields.Many2one('product.category', string='Product Category')