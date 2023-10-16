# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from os.path import join, dirname, realpath
from odoo import api, SUPERUSER_ID
import csv


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([])
    companies.point_of_sale_update_stock_quantities = 'real'
