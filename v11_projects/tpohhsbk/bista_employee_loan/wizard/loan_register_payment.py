# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode


class LoanRegisterPaymentWizard(models.TransientModel):
    _name = "loan.register.payment.wizard"
    _description = "Loan Register Payment wizard"

    @api.model
    def _default_partner_id(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        loan_record = self.env['hr.employee.loan'].browse(active_id)
        partner = loan_record.employee_id.partner_id.id or False
        return partner

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, default=_default_partner_id)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.one
    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.journal_id.outbound_payment_method_ids
        self.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            return {'domain': {'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}
        return {}

    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication
        }

    @api.multi
    def loan_post_payment(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        loan_record = self.env['hr.employee.loan'].browse(active_id)
        loan_installment_ids = loan_record.loan_installment_ids.filtered(lambda l:l.select_loan)
        if sum(loan_installment_ids.mapped('amount')) != self.amount:
               raise ValidationError(_('Amount should be match with selected installment amount'))

        # Create JE and Make it Post and Reconcile
        self.create_account_move(loan_record)

        # Create payment and post it
#         payment = self.env['account.payment'].create(self._get_payment_vals())
#         payment.post()

#         # Log the payment in the chatter
#         body = (_("A payment of %s %s with the reference <a "
#                   "href='/mail/view?%s'>%s</a> related to your loan %s has "
#                   "been made.")
#                 % (payment.amount, payment.currency_id.symbol,
#                    url_encode({'model': 'account.payment',
#                                'res_id': payment.id}),
#                    payment.name, loan_record.name))
#         loan_record.message_post(body=body)

        # Reconcile the payment and the loan_record, i.e. lookup on the payable account move lines
#         account_move_lines_to_reconcile = self.env['account.move.line']
#         for line in payment.move_line_ids + loan_record.account_move_id.line_ids:
#             if line.account_id.internal_type == 'receivable':
#                 account_move_lines_to_reconcile |= line
#         account_move_lines_to_reconcile.reconcile()

        loan_installment_ids.write({'state': 'done', 'paid_date': fields.Date.today(), 'select_loan':False})
        if all(loan_statement.state == 'done' for loan_statement in loan_record.loan_installment_ids):
            loan_record.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def create_account_move(self, loan_record):
        ''' Create a Journal entry for installment loan amount'''
        move = self.env['account.move'].create({
            'journal_id':self.journal_id.id,
            'company_id':loan_record.company_id.id,
            'date': self.payment_date,
            'ref': self.communication,
            'name': '/',
        })
        if move:
            move_line_lst = self._prepare_move_lines(move, loan_record)
            move.line_ids = move_line_lst
            loan_record.write({'move_ids':[(4, move.id)]})
#             move.post()

    def _prepare_move_lines(self, move, loan_record):
        ''' Create journal Items '''
        move_lst = []
        if not loan_record.loan_journal_id.default_debit_account_id and not loan_record.loan_journal_id.default_credit_account_id:
            raise Warning(_('journal %s have must be Default Credit and Debit account.') % (loan_record.journal_id.name))

        partner = loan_record.employee_id.partner_id.id if loan_record.employee_id.partner_id else False
        generic_dict = {
#             'name': self.name,
            'company_id':loan_record.company_id.id,
            'currency_id':loan_record.company_id.currency_id.id,
            'date_maturity': loan_record.loan_issuing_date,
            'journal_id':self.journal_id.id,
            'date': self.payment_date,
            'partner_id': partner,
            'quantity': 1,
            'move_id': move.id,
        }
        debit_entry_dict = {
            'account_id': self.journal_id.default_debit_account_id.id,
            'debit': self.amount,
        }
        credit_entry_dict = {
            'account_id':loan_record.credit_account_id.id,
            'credit': self.amount,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst
