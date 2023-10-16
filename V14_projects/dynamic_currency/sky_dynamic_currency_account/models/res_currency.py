# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp


class ResCurrency(models.Model):
      
    _inherit = 'res.currency'
      
    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        """
            Conversion with custom rate
        """
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        if self._context.get('rate'):
            from_currency_rate = self._context.get('rate')
        else:
            from_currency_rate = currency_rates.get(from_currency.id)
        res = currency_rates.get(to_currency.id) / from_currency_rate
        return res
