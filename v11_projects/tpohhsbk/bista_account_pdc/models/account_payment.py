# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.register.payments"

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')
    check_number_char = fields.Char(string="Check Number", copy=False,
                                    help="Number of the check corresponding to this payment. If your pre-printed check are not already numbered, "
                                         "you can manage the numbering in the journal configuration page.")

    @api.constrains('check_number_char')
    def change_check_number(self):
        for rec in self:
            if rec.check_number_char and not rec.check_number_char.isdigit():
                raise ValidationError("Check Number Must Be Integer Only!")
            else:
                rec.check_number = int(rec.check_number_char)

    def get_payments_vals(self):
        res = super(AccountRegisterPayment, self).get_payments_vals()
        if self.payment_method_id == self.env.ref('account_check_printing.account_payment_method_check') or self.payment_method_code == 'pdc':
            for rec in res:
                rec.update({
                    'cheque_date': self.cheque_date,
                    'related_journal': self.related_journal and self.related_journal.id or False,
                    'check_number_char': str(self.check_number)
                })
            if self.env['ir.module.module'].sudo().search(
                    [('name', '=', 'account_check_printing'), ('state', '=', 'installed')]):
                if self.payment_method_code == 'pdc' and self.journal_id.check_manual_sequencing:
                    self.journal_id.check_sequence_id.next_by_id()
        return res

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if hasattr(super(AccountRegisterPayment, self), '_onchange_journal_id'):
            super(AccountRegisterPayment, self)._onchange_journal_id()
        if self.env['ir.module.module'].sudo().search(
                [('name', '=', 'account_check_printing'), ('state', '=', 'installed')]):
            if self.journal_id.check_manual_sequencing:
                self.check_number_char = self.journal_id.check_sequence_id.number_next_actual



class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_cancel(self):
        ''' 
            Pass the with_context "custom_move" to allowed to delete JE and make invoice cancel.
        '''
        return super(account_invoice,self.with_context(custom_move=True)).action_invoice_cancel()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')
    pdc_reconciled = fields.Boolean(copy=False, string='Pdc Reconciled')
    pdc_manual_payment = fields.Boolean(compute='_compute_pdc_type',
                                        copy=False,
                                        string='Display PDC Payment Button')
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    check_number_char = fields.Char(string="Check Number", copy=False,
                                    help="Number of the check corresponding to this payment. If your pre-printed check are not already numbered, "
                                         "you can manage the numbering in the journal configuration page.")

    @api.multi
    def cancel(self):
        ''' 
            Pass the with_context "custom_move" to allowed to delete the payment JE.
        '''
        return super(AccountPayment,self.with_context(custom_move=True)).cancel()

    @api.constrains('check_number_char')
    def change_check_number(self):
        for rec in self:
            if rec.check_number_char and not rec.check_number_char.isdigit():
                raise ValidationError("Check Number Must Be Integer Only!")
            else:
                rec.check_number = int(rec.check_number_char)

    @api.multi
    def action_pdc(self):
        '''
        This will open a pop up where you can update effective date.
        '''
        for rec in self:
            view_id = self.env.ref(
                'bista_account_pdc.wiz_view_account_pdc_form')
            return {
                'name': 'Account pdc Payment ',
                'type': 'ir.actions.act_window',
                'view_id': view_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wiz.pdc.payment',
                'target': 'new',
            }

    @api.depends()
    def _compute_pdc_type(self):
        '''
        sets pdc payment button true when pdc_type in account settings is set
        manual.
        '''
        account_pdc_type = self.company_id.pdc_type
        if not self.pdc_reconciled:
            if account_pdc_type == 'manual':
                self.pdc_manual_payment = True

    @api.model
    def account_pdc(self):
        '''
            This is scheduler method, will search Payments which in which
            Payment method is PDC and effective date is equal to today than it
            will create PDC JE and reconcile PDC entries.
        '''
        for company in self.env['res.company'].search([('pdc_type','=','automatic')]):
            rec = self.search([
                ('cheque_date', '=',datetime.today().date()),
                               ('pdc_reconciled', '=', False),
                               ('company_id','=',company.id),
                               ('payment_method_code', '=', 'pdc')
                               ])
            self.create_move(rec)

    def _get_move_vals(self, journal=None):
        '''
        This method will use to create check number in JE.
        '''
        res = super(AccountPayment, self)._get_move_vals(journal)
        res['check_number_char'] = self.check_number_char
        return res

    @api.multi
    def post(self):
        '''
            This method will check Payment method is PDC and effective date is
            less or equal to today than it will create PDC JE and reconcile PDC
            entries.
        '''
        res = super(AccountPayment, self).post()
        for rec in self:
            if rec.payment_method_code == 'pdc':
                if rec.cheque_date <= str(datetime.today().date()):
                    rec.create_move(rec)
        return res

    @api.multi
    def create_move(self, res):
        '''
        This method will create JE for PDC and also reconcile PDC entries.
        '''
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for rec in res:
            if rec.partner_type == 'customer':
                mv1_debit = rec.amount
                mv1_credit = 0.0
                mv2_debit = 0.0
                mv2_credit = rec.amount

            if rec.partner_type == 'supplier':
                mv1_debit = 0.0
                mv1_credit = rec.amount
                mv2_debit = rec.amount
                mv2_credit = 0.0

            move_line_1 = {
                'account_id':
                    rec.related_journal.default_debit_account_id.id,
                'name': '/',
                'debit': mv1_debit,
                'credit': mv1_credit,
                'partner_id': rec.partner_id.id,
                'company_id': rec.company_id.id,
                'date_maturity': rec.cheque_date,
                'name':'PDC Payment',
            }
            move_line_2 = {
                'account_id': rec.journal_id.default_credit_account_id.id,
                'name': rec.check_number,
                'credit': mv2_credit,
                'debit': mv2_debit,
                'partner_id': rec.partner_id.id,
                'company_id': rec.company_id.id,
                'date_maturity': rec.cheque_date,
                'name': 'Vendor Payment',
            }
            move = account_move_obj.create({
                'journal_id': rec.related_journal.id,
                'date': rec.cheque_date,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                'ref': rec.communication or rec.check_number,
                'check_number_char': rec.check_number
            })
            move.post()
            rec.state = 'posted'
            # search move lines of PDC, to reconcile
            if rec.partner_type == 'customer':
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('credit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('debit', '!=', 0.0)])
            if rec.partner_type == 'supplier':
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('debit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('credit', '!=', 0.0)])
            # reconcile move lines
            move_lines_filtered = move_lines.filtered(
                lambda aml: not aml.reconciled)
            move_lines_filtered.with_context(
                skip_full_reconcile_check='amount_currency_excluded'
            ).reconcile()
            move_lines.force_full_reconcile()
            rec.pdc_reconciled = True
            rec.move_line_ids += move.line_ids

    @api.multi
    def cheque_bounce(self):
        '''
         This will raise warning if effective date is greater than current date
         else it will unlink move and set state as draft.
        '''
        for payment_rec in self:
            if payment_rec.cheque_date > str(datetime.today().date()):
                raise ValidationError(_(
                    "Check can not bounce before effective date."))
            payment_rec.cancel()
            payment_rec.state = 'draft'

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if hasattr(super(AccountPayment, self), '_onchange_journal_id'):
            super(AccountPayment, self)._onchange_journal_id()
        if self.env['ir.module.module'].sudo().search(
                [('name', '=', 'account_check_printing'), ('state', '=', 'installed')]):
            if self.journal_id.check_manual_sequencing:
                self.check_number_char = self.journal_id.check_sequence_id.number_next_actual


class PrintPreNumberedChecks(models.TransientModel):
    _inherit = 'print.prenumbered.checks'

    next_check_number = fields.Char('Next Check Number', required=True)

    @api.multi
    def print_checks(self):
        check_number = 0
        if self.next_check_number and not self.next_check_number.isdigit():
            raise ValidationError("Check Number Must Be Integer Only!")
        else:
            check_number = int(self.next_check_number)
        payments = self.env['account.payment'].browse(self.env.context['payment_ids'])
        payments.filtered(lambda r: r.state == 'draft').post()
        payments.filtered(lambda r: r.state not in ('sent', 'cancelled')).write({'state': 'sent'})
        for payment in payments:
            payment.check_number_char = str(check_number)
            check_number += 1
        return payments.do_print_checks()
