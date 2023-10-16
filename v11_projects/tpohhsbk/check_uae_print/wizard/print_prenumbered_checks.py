# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrintPreNumberedChecks(models.TransientModel):
    _inherit = 'print.prenumbered.checks'

    check_format_id = fields.Many2one('cheque.format', string="Cheque Format")
    next_number = fields.Integer("Next Check Number", compute="get_next_cheque_number")


    # @api.multi
    # def print_checks(self):
    #     res = super(PrintPreNumberedChecks, self).print_checks()
    #
    #     if self.env.context['payment_ids']:
    #         payments = self.env['account.payment'].browse(self.env.context['payment_ids'])
    #         if payments:
    #             payments.write({'check_format_id': self.check_format_id.id})
    #
    #         # for payment in payments:
    #         #     if payment.journal_id.account_checkbook_id:
    #         #         if payment.journal_id.account_checkbook_id.printed_page == 0:
    #         #             payment.journal_id.account_checkbook_id.printed_page = payment.journal_id.account_checkbook_id.start_page
    #         #         else:
    #         #             payment.journal_id.account_checkbook_id.printed_page = payment.journal_id.account_checkbook_id.printed_page + 1
    #     return res
