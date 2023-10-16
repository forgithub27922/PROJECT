# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api


class res_currency(models.Model):
    _inherit = "res.currency"

    inverse_rate = fields.Float(
        'Current Inverse Rate', digits=(12, 4),
        compute='get_inverse_rate',
        help='The rate of the currency from the currency of rate 1 (0 if no '
                'rate defined).'
    )

    @api.depends('rate')
    def get_inverse_rate(self):
        for rec in self:
            rec.inverse_rate = rec.rate and (
            1.0 / (rec.rate))

    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 12),
                        help='The rate of the currency to the currency of rate 1.')


class res_currency_rate(models.Model):
    _inherit = "res.currency.rate"
    rate = fields.Float(string='Current Rate', digits=(12, 12),)

    inverse_rate = fields.Float(
        'Inverse Rate', digits=(12, 4),
        compute='get_inverse_rate',
        inverse='set_inverse_rate',
        help='The rate of the currency from the currency of rate 1',
    )

    @api.depends('rate')
    def get_inverse_rate(self):
        for rec in self:
            rec.inverse_rate = rec.rate and (1.0 / (rec.rate))

    def set_inverse_rate(self):
        for rec in self:
            rec.rate = rec.inverse_rate and (1.0 / (rec.inverse_rate))

