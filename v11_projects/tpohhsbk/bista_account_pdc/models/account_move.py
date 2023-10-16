# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    show_check_number = fields.Boolean(string="Show Check NO",
                                       compute='_show_check_number', store=True)
    date = fields.Date(required=True, states={'posted': [('readonly', True)]},
                       index=True, copy=False, default=fields.Date.context_today)
    check_number = fields.Integer('Check Number')
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

    @api.depends('journal_id')
    def _show_check_number(self):
        for rec in self:
            if rec.journal_id.outbound_payment_method_ids.filtered(lambda l:l.code in ['check_printing', 'pdc']):
                rec.show_check_number = True

    @api.multi
    def unlink(self):
        '''
        Purpose of override the unlink method to restric the JE once the number
        is generated either JE in Posted or Unposted State.
        self._context.get('custom_move')
        We use with_context({'custom_move':True}) for all over custom object
        while Unlink Journal entry.
        '''
        for move in self:
            if move.name and move.name != '/' and not self._context.get('custom_move'):
                raise ValidationError(_("You can't delete the Journal Entry once the number generated."))
        return super(AccountMove, self).unlink()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    set_analytic_required = fields.Boolean(string="Set Analytic Field Mandatory",
                                           compute='_set_analytic_required', store=True)
    date_maturity = fields.Date(
        string='Due date', index=True,
        required=True,
        copy=False,
        help="This field is used for payable and receivable journal entries. "
             "You can put the limit date for the payment of this line.")

    @api.model
    def create(self,vals):
        res = super(AccountMoveLine,self).create(vals)
        if res.company_id.analytic_account_id and not res.analytic_account_id:
            res.set_default_company_cost_center()
        return res

    @api.depends('account_id')
    def _set_analytic_required(self):
        for rec in self:
            if rec.account_id.user_type_id.filtered(lambda l:l.name in ['Income', 'Expenses']):
                rec.set_analytic_required = True

    @api.multi
    def set_default_company_cost_center(self):
        '''
            This Function set default cost center for the 
            asset and liabilities type of account.
        '''
        self = self.sudo()
        assets_liabilities_type_obj = self.env['account.account.type'].sudo()
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_receivable')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_liquidity')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_current_assets')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_non_current_assets')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_fixed_assets')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_equity')

        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_current_liabilities')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_non_current_liabilities')
        assets_liabilities_type_obj |= self.env.ref('account.data_account_type_payable')

        if self.account_id.user_type_id.id in assets_liabilities_type_obj.ids:
            self.with_context(check_move_validity=False).write({'analytic_account_id':self.company_id.analytic_account_id.id})


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    set_analytic_required = fields.Boolean(string="Set Analytic Field Mandatory",
                                           compute='_set_analytic_required', store=True)

    @api.depends('account_id')
    def _set_analytic_required(self):
        for rec in self:
            if rec.account_id.user_type_id.name == 'Expenses':
                rec.set_analytic_required = True


class res_company(models.Model):
  _inherit = 'res.company'

  analytic_account_id = fields.Many2one('account.analytic.account',string="Analytic Account",
            help="Get Default Cost Center for Asset/Liabilities Type account.")

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.multi
    def button_cancel_reconciliation(self):
        aml_to_unbind = self.env['account.move.line']
        aml_to_cancel = self.env['account.move.line']
        payment_to_unreconcile = self.env['account.payment']
        payment_to_cancel = self.env['account.payment']
        for st_line in self:
            aml_to_unbind |= st_line.journal_entry_ids
            for line in st_line.journal_entry_ids:
                payment_to_unreconcile |= line.payment_id
                if st_line.move_name and line.payment_id.payment_reference == st_line.move_name:
                    # there can be several moves linked to a statement line but maximum one created by the line itself
                    aml_to_cancel |= line
                    payment_to_cancel |= line.payment_id
        aml_to_unbind = aml_to_unbind - aml_to_cancel

        if aml_to_unbind:
            aml_to_unbind.write({'statement_line_id': False})

        payment_to_unreconcile = payment_to_unreconcile - payment_to_cancel
        if payment_to_unreconcile:
            payment_to_unreconcile.unreconcile()

        if aml_to_cancel:
            aml_to_cancel.remove_move_reconcile()
            moves_to_cancel = aml_to_cancel.mapped('move_id')
            moves_to_cancel.button_cancel()
            moves_to_cancel.with_context(custom_move=True).unlink()
        if payment_to_cancel:
            payment_to_cancel.unlink()