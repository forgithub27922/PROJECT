# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        invoice_vals = super()._onchange_invoice_date()
        print("invoice_vals:::::::::::::::::", invoice_vals, self.invoice_date)
        if self.invoice_date:
            if self.is_purchase_document():
                self._onchange_currency()
        return invoice_vals
