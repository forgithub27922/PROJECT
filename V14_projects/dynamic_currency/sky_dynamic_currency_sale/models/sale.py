# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Sale(models.Model):
    _inherit = 'sale.order'

    rate = fields.Float('Current Inverse Rate',digits=(7, 9))

    def _create_invoices(self, grouped=False, final=False, date=None):
        print("\n\n\n YES I'm Call")
        invoice = super(Sale, self)._create_invoices()
        if self.rate:
            print("\n\n RATE :::::::::>>>>>>>>>>>>>>>>", self.rate)
            invoice.update({'manual_currency_rate_active': True,
                            'inverse_rate': self.rate,
                            'currency_id': self.currency_id.id})
            invoice.change_inverse_rate()
            invoice.change_currency_rate()
