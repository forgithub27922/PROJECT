# -*- coding: utf-8 -*-

from odoo import models, fields


class PriceRule(models.Model):
    _inherit = 'delivery.price.rule'

    variable = fields.Selection(selection_add=[('net_price', 'Netto Price')])
