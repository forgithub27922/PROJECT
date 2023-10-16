# -*- coding: utf-8 -*-
from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('invoice_id.invoice_line_ids')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.invoice_id.invoice_line_ids:
                no += 1
                l.sequence_ref = no