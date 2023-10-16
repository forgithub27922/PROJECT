# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PettyCashDocument(models.Model):
    _name = 'petty.cash.document'
    _description = "Pettycash Documents"

    name = fields.Char('Description', required=True)
    file = fields.Binary(string="File")
    date = fields.Date(string="Date", required=True,
                       default=fields.Date.context_today)
    pettycash_id = fields.Many2one('voucher.petty.cash', 'Petty Cash ID')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class VoucherPettyCash(models.Model):
    _name = 'voucher.petty.cash'
    _inherit = ['mail.thread']
    _description = "Petty Cash Voucher"
    _rec_name = 'reference'
    _order = 'date desc'

    @api.multi
    def _get_move_line_count(self):
        payment_obj = self.env['account.move.line']
        for rec in self:
            payment_ids = payment_obj.search([('pettycash_id', '=', rec.id)])
            rec.move_line_count = len(payment_ids)

    @api.one
    @api.depends('expense_ids', 'invoice_ids', 'amount', 'state', 'pay_type')
    def _compute_total(self):
        self.advance_paid = self.amount
        expense_amount = 0.0
        if self.pay_type == 'partner' and self.invoice_ids:
            expense_amount = sum(inv.amount_total for inv in
                                 self.invoice_ids.filtered(
                                     lambda x: x.state != 'cancel'))
        elif self.pay_type == 'employee' and self.expense_ids:
            expense_amount = sum(expense.total_amount for expense in
                                 self.expense_ids.filtered(
                                     lambda x: x.state != 'refused'))
        self.total_expense = expense_amount
        self.total_difference = self.advance_paid - self.total_expense
        type_res = 'pay'
        if self.total_difference > 0:
            type_res = 'collect'
        if self.total_difference == 0:
            type_res = 'reconcile'
        self.capital_type = type_res
        residual = abs(self.total_difference)
        if self.state == 'reconciled':
            residual = 0.0
        self.residual = residual


    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  track_visibility='onchange')
    payment_type = fields.Selection([
        ('outbound', 'Send Money')],
        # ('inbound', 'Receive Money')
        string='Petty Cash Type', default='outbound',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        help="Use for sending money or receiving money.")
    payment_mode = fields.Selection([('cash', 'Cash'),
                                     ('bank', 'Bank')], string='Payment Mode',
                                    default='cash',
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    track_visibility='onchange')
    reference = fields.Char('Reference', copy=False)
    bank_ref = fields.Char('Bank Ref./Check Number', copy=False, readonly=True,
                            states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Partner',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('customer', '=', False)]",
                                 track_visibility='onchange')
    amount = fields.Float('Amount', readonly=True,
                            states={'draft': [('readonly', False)]},
                            track_visibility='onchange', copy=False)
    date = fields.Date('Date', default=fields.Date.context_today,
                       required=True, readonly=True,
                       states={'draft': [('readonly', False)]},
                       track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  required=True, readonly=True,
                                  default = lambda self:
                                  self.env.user.company_id.currency_id,
                                  states={'draft': [('readonly', False)]},
                                  track_visibility='onchange')
    account_id = fields.Many2one('account.account',
                                 string='Petty Cash Account',
                                 required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 track_visibility='onchange',
                                 help="Petty cash credit account.")
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('approved_manager', 'Approved by Manager'),
                              ('approved_hr', 'Approved by HR'),
                              ('approved_finance', 'Approved by Finance'),
                              ('paid', 'Paid'),
                              ('reconciled', 'Reconciled')],
                             string='Status', default='draft',
                             required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             track_visibility='always')
    notes = fields.Text('Description')
    document_ids = fields.One2many('petty.cash.document', 'pettycash_id',
                                   string='Documents')
    move_line_ids = fields.One2many('account.move.line', 'pettycash_id',
                                    string='Payment', copy=False)
    move_line_count = fields.Integer(string='# of Payments', readonly=True,
                                     compute='_get_move_line_count')
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',
                              default=lambda self: self.env.user,
                              readonly=True, required=True,
                              help='By which users created the record.')
    pay_type = fields.Selection([('partner', 'Partner'), ('employee', 'Employee')], default="partner",
                                string="Pay To",readonly=True,
                                states={'draft': [('readonly', False)]},)
    expense_ids = fields.One2many('hr.expense', 'pettycash_id',
                                  string='Expenses', copy=False)
    invoice_ids = fields.One2many('account.invoice', 'pettycash_id',
                                  string='Bills', copy=False)
    advance_paid = fields.Float(compute='_compute_total',
                                string='Advance Paid', copy=False)
    total_expense = fields.Float(compute='_compute_total',
                                 string='Total Expense', copy=False)
    total_difference = fields.Float(
        compute='_compute_total', string='Difference', copy=False,
        help="+ : Return money from Employee/Partner. \n"
             "- : Collect money from Employee/Partner.")
    residual = fields.Float(
        compute='_compute_total', string='Amount Due', copy=False,
        help="In Paid state show will be difference amount.\n"
             "In Residual state amount due show will be zero.")
    capital_type = fields.Selection([('collect', 'Collect'),
                                     ('pay', 'Pay'),
                                     ('reconcile', 'Reconcile')],
                                    compute='_compute_total',
                                    string='Capital Type',
                                    help="After Paid state money will be "
                                         "collect or pay to Employee/Partner.")

    @api.onchange('pay_type')
    def onchange_pay_type(self):
        if self.pay_type and self.pay_type == 'partner':
            self.employee_id = False
            self.expense_ids = []
        if self.pay_type and self.pay_type == 'employee':
            self.partner_id = False
            self.invoice_ids = []

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id and not self.employee_id.partner_id:
            raise ValidationError(_("Employee have no partner!"))
        if self.employee_id and self.employee_id.partner_id:
            self.partner_id = self.employee_id.partner_id.id or False

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        self.journal_id = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.account_id = False
        if self.partner_id:
            self.account_id = self.partner_id.property_account_payable_id.id

    @api.multi
    def action_submit_request(self):
        if not self.amount:
            raise ValidationError(_("Amount must be greater than zero!"))
        self.write({'state': 'submit'})

    @api.multi
    def action_approve_by_manager(self):
        self.write({'state': 'approved_manager'})

    @api.multi
    def action_approve_by_hr(self):
        self.write({'state': 'approved_hr'})

    @api.multi
    def action_approve_by_finance(self):
        self.write({'state': 'approved_finance'})

    @api.multi
    def action_paid(self):
        for rec in self:
            moves = rec._create_move()
            self.write({'state': 'paid'})
        return True

    @api.multi
    def action_pay_remain(self):
        '''
        :return: Pay remain amount to employee or partner.
        '''
        for rec in self:
            moves = rec._create_move()
        return True

    @api.multi
    def action_reconcile(self):
        '''
        :return: Reconcile.
        '''
        self.ensure_one()
        if any(expense.state != 'done' for expense in
               self.expense_ids.filtered(lambda x: x.state != 'refused')):
            raise UserError(_("Nothing to Reconcile: Please check Expenses "
                              "should be Approved and Posted!"))
        if any(invoice.state != 'open' for invoice in
               self.invoice_ids.filtered(lambda x: x.state != 'cancel')):
            raise UserError(_("Nothing to Reconcile: Please check Bills "
                              "should be Validated!"))


        # Reconciled entries.
        pettycash_mvl = self.env['account.move.line']
        nmvl = self.env['account.move.line']
        if self.pay_type == 'employee':
            for expense in self.expense_ids:
                if expense.sheet_id and expense.sheet_id.account_move_id:
                    nmvl += expense.sheet_id.account_move_id.line_ids
        if self.pay_type == 'partner':
            for invoice in self.invoice_ids:
                if invoice.move_id and invoice.move_id.line_ids:
                    nmvl += invoice.move_id.line_ids

        nmvl += self.env['account.move.line'].search([
            ('pettycash_id', '=', self.id)])

        for nmv_line in nmvl:
            if not nmv_line.pettycash_id:
                nmv_line.write({'pettycash_id': self.id})
            if nmv_line.account_id.user_type_id.type in \
                ('receivable', 'payable'):
                if nmv_line not in pettycash_mvl:
                    pettycash_mvl += nmv_line
        if pettycash_mvl:
            pettycash_mvl.reconcile()
        self.write({'state': 'reconciled'})
        return True

    @api.model
    def _create_move(self):
        '''
        :return: Pay Patty-cash to employee.
        '''
        ctx = (self._context)
        journal_rec = self.journal_id or False
        partner_rec = self.partner_id or False
        payment_type = self.payment_type
        if not partner_rec:
            raise ValidationError(_("Employee have no partner!"))
        partner_name = partner_rec.name
        res_payment_type = \
            'Send Money' if payment_type and payment_type == 'outbound' \
                else 'Receive Money'

        #Multi currency.
        amt = self.amount
        allow_reconcile = False
        if self.state == 'paid' and self.capital_type == 'pay':
            amt = abs(self.total_difference)
            allow_reconcile = True

            # If added expenses is not post then not allow to further process,
            # Because need for reconcile lines(Advance - expense= Remain)
            if any(expense.state != 'done' for expense in
                   self.expense_ids.filtered(lambda x: x.state != 'refused')):
                raise UserError(_("Expenses must be Post or Refused!"))
            if any(invoice.state != 'open' for invoice in
                   self.invoice_ids.filtered(lambda x: x.state != 'cancel')):
                raise UserError(_("Bills must be in Open state!"))

        company_currency = self.company_id.currency_id
        diff_currency = self.currency_id != company_currency
        if self.currency_id != company_currency:
            amount_currency = self.currency_id.with_context(ctx).\
                compute(amt, company_currency)
        else:
            amount_currency = False

        debit, credit, amount_currency, dummy = self.env['account.move.line']\
            .with_context(date=self.date).compute_amount_fields(
            amt, self.currency_id, self.company_id.currency_id)

        debit_vals = {
            'name': partner_name + ':' + res_payment_type,
            'debit': abs(debit),
            'credit': 0.0,
            'account_id': self.account_id.id,
            'amount_currency': diff_currency and amount_currency,
            'currency_id': diff_currency and self.currency_id.id,
            'pettycash_id': self.id,
            'partner_id': partner_rec.id or False,
        }
        credit_vals = {
            'name': 'Petty Cash',
            'debit': 0.0,
            'credit': abs(debit),
            'account_id':
                journal_rec.default_debit_account_id
                and journal_rec.default_debit_account_id.id or False,
            'amount_currency': diff_currency and -amount_currency,
            'currency_id': diff_currency and self.currency_id.id,
            'pettycash_id': self.id,
        }
        vals = {
            'journal_id': journal_rec.id,
            'date': fields.date.today(),
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Petty Cash - Send'
        }
        move = self.env['account.move'].create(vals)
        move.post()

        # Create chatter.
        title = 'Send Pettty Cash'
        if allow_reconcile:
            title = 'Send Petty Cash (Remain)'
        message = ('''%s :
                        <ul class="o_mail_thread_message_tracking">
                            <li>Date: %s</li>
                            <li>Amount: %s</li>
                        </ul>
                    ''') % (title, self.date, amt)
        self.message_post(body=message)

        # Reconciled entries.
        if allow_reconcile:
            pettycash_mvl = self.env['account.move.line']
            nmvl = self.env['account.move.line']
            if self.pay_type == 'employee':
                for expense in self.expense_ids:
                    if expense.sheet_id and expense.sheet_id.account_move_id:
                        nmvl += expense.sheet_id.account_move_id.line_ids
            if self.pay_type == 'partner':
                for invoice in self.invoice_ids:
                    if invoice.move_id and invoice.move_id.line_ids:
                        nmvl += invoice.move_id.line_ids

            nmvl += self.env['account.move.line'].search([
                ('pettycash_id', '=', self.id)])

            for nmv_line in nmvl:
                if not nmv_line.pettycash_id:
                    nmv_line.write({'pettycash_id': self.id})
                if nmv_line.account_id.user_type_id.type in \
                    ('receivable', 'payable'):
                    if nmv_line not in pettycash_mvl:
                        pettycash_mvl += nmv_line
            if pettycash_mvl:
                pettycash_mvl.reconcile()
            self.write({'state': 'reconciled'})
        return move

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['reference'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                    'voucher.petty.cash') or _('New')
            else:
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'voucher.petty.cash') or _('New')
        res = super(VoucherPettyCash, self).create(vals)
        if res.expense_ids:
            if res.employee_id:
                expense_sheet_vals = {
                    'name': res.employee_id.name + ' Expense' + '(' + res.date + ')',
                    'employee_id': res.employee_id.id,
                    'payment_mode': 'own_account',
                    'pettycash_id': res.id}
                hr_expense_sheet_id = self.env['hr.expense.sheet'].create(
                    expense_sheet_vals)
                for expense in res.expense_ids:
                    hr_expense_sheet_id.with_context({'from_create': True}).\
                        write({'expense_line_ids': [(4, expense.id)]})
        if res.invoice_ids:
            res.invoice_ids.write({'type': 'in_invoice'})
        return res

    @api.multi
    def write(self, vals):
        res = super(VoucherPettyCash, self).write(vals)
        if vals.get('expense_ids', []):
            expense_sheet_obj = self.env['hr.expense.sheet']
            for pettycash in self:
                hr_expense_sheet_id = expense_sheet_obj.search([
                    ('pettycash_id', '=', pettycash.id),
                    ('state', '=', 'draft')], limit=1)
                if hr_expense_sheet_id:
                    for expense in pettycash.expense_ids:
                        hr_expense_sheet_id.write(
                            {'expense_line_ids': [(4, expense.id)]})
                if not hr_expense_sheet_id:
                    for expense_rec in vals.get('expense_ids'):
                        hr_expense_sheet_id = expense_sheet_obj.search([
                            ('pettycash_id', '=', pettycash.id),
                            ('state', '=', 'draft')], limit=1)
                        if not hr_expense_sheet_id and expense_rec[0] == 0:
                            expense_sheet_vals = {
                                'name': pettycash.employee_id.name +
                                        ' Expense' + '(' +pettycash.date+ ')',
                                'employee_id': pettycash.employee_id.id,
                                'payment_mode': 'own_account',
                                'pettycash_id': pettycash.id}
                            hr_expense_sheet_id = expense_sheet_obj.\
                                create(expense_sheet_vals)
                    for expense in pettycash.expense_ids:
                        hr_expense_sheet_id.write({
                            'expense_line_ids': [(4, expense.id)]})
        for pettycash in self:
            if pettycash.invoice_ids:
                pettycash.invoice_ids.write({'type': 'in_invoice'})
        return res

    @api.multi
    def action_view_documents(self):
        '''
        :return: View documents.
        '''
        self.ensure_one()
        ctx = dict(self._context)
        action = self.env.ref('bista_petty_cash.action_pettycash_document')
        ctx.update({'default_pettycash_id': self.id})
        return {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': ctx,
            'domain': [('pettycash_id', '=', self.id)],
            'res_model': action.res_model,
        }

    @api.multi
    def action_view_entries(self):
        '''
        :return: View journal entries.
        '''
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_a')
        return {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': self._context,
            'domain': [('id', '=', self.move_line_ids.ids)],
            'res_model': action.res_model,
        }

    @api.multi
    def action_return_pettycash(self):
        '''
        :return: Open Wizard for return Petty-Cash.
        '''
        self.ensure_one()
        ctx = dict(self._context)
        ctx.update({'default_amount': self.total_difference})

        if any(expense.state != 'done' for expense in
               self.expense_ids.filtered(lambda x: x.state != 'refused')):
            raise UserError(_("Expenses must be Post or Refused!"))
        if any(invoice.state != 'open' for invoice in
               self.invoice_ids.filtered(lambda x: x.state != 'cancel')):
            raise UserError(_("Bills must be in Open state!"))

        form_view = self.env.ref('bista_petty_cash.view_return_pettycash_form')
        return {
            'name': 'Return Petty Cash',
            'type': 'ir.actions.act_window',
            'view_id': form_view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'return.petty.cash',
            'target': 'new',
            'context': ctx,
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pettycash_id = fields.Many2one('voucher.petty.cash', 'Journal Item')