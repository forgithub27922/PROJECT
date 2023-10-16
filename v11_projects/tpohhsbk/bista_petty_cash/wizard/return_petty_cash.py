# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ReturnPettyCash(models.TransientModel):
    _name = 'return.petty.cash'
    _description = "Return Petty Cash"

    date = fields.Date('Date', default=fields.date.today(), required=True)
    amount = fields.Float('Amount', required=True)

    @api.multi
    def action_reverse_entry(self):
        self.ensure_one()
        context = self._context
        pettycash_obj = self.env['voucher.petty.cash']
        active_record = pettycash_obj.browse(context.get('active_id'))

        journal_rec = active_record.journal_id or False
        partner_rec = active_record.partner_id or False
        payment_type = active_record.payment_type
        partner_name = partner_rec.name
        res_payment_type = \
            'Send Money' if payment_type and payment_type == 'outbound' \
                else 'Receive Money'

        # Multi currency.
        company_currency = active_record.company_id.currency_id
        diff_currency = active_record.currency_id != company_currency
        if active_record.currency_id != company_currency:
            amount_currency = active_record.currency_id.with_context(context). \
                compute(self.amount, company_currency)
        else:
            amount_currency = False

        debit, credit, amount_currency, dummy = self.env['account.move.line'] \
            .with_context(date=active_record.date).compute_amount_fields(
            self.amount, active_record.currency_id,
            active_record.company_id.currency_id)

        debit_vals = {
            'name': 'Petty Cash',
            'debit': abs(debit),
            'credit': 0.0,
            'account_id':
                journal_rec.default_credit_account_id
                and journal_rec.default_credit_account_id.id or False,
            'amount_currency': diff_currency and amount_currency,
            'currency_id': active_record.currency_id.id or False,
            'pettycash_id': active_record.id
        }
        credit_vals = {
            'name': partner_name + ':' + res_payment_type,
            'debit': 0.0,
            'credit': abs(debit),
            'account_id': active_record.account_id.id,
            'amount_currency': diff_currency and -amount_currency,
            'currency_id': active_record.currency_id.id or False,
            'pettycash_id': active_record.id,
            'partner_id': partner_rec.id or False,
        }
        vals = {
            'journal_id': journal_rec.id,
            'date': self.date,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Petty Cash - Receive'
        }
        move = self.env['account.move'].create(vals)
        move.post()
        # Create chatter.
        message = ('''Return Pettty Cash :
                        <ul class="o_mail_thread_message_tracking">
                            <li>Date: %s</li>
                            <li>Amount: %s</li>
                        </ul>
                    ''') % (self.date, self.amount)
        active_record.message_post(body=message)

        # Reconciled entries.
        pettycash_mvl = self.env['account.move.line']
        nmvl = self.env['account.move.line']
        if active_record.pay_type == 'employee':
            for expense in active_record.expense_ids:
                if expense.sheet_id and expense.sheet_id.account_move_id:
                    nmvl += expense.sheet_id.account_move_id.line_ids
        if active_record.pay_type == 'partner':
            for invoice in active_record.invoice_ids:
                if invoice.move_id and invoice.move_id.line_ids:
                    nmvl += invoice.move_id.line_ids

        nmvl += self.env['account.move.line'].search([
            ('pettycash_id', '=', active_record.id)])

        for nmv_line in nmvl:
            if not nmv_line.pettycash_id:
                nmv_line.write({'pettycash_id': active_record.id})
            if nmv_line.account_id.user_type_id.type in \
                ('receivable', 'payable'):
                if nmv_line not in pettycash_mvl:
                    pettycash_mvl += nmv_line
        if pettycash_mvl:
            pettycash_mvl.reconcile()
        active_record.write({'state': 'reconciled'})
        return True