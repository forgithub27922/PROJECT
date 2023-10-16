# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, Warning


class batch_employee_loan(models.Model):
    _name = 'batch.employee.loan'
    _inherit = ['mail.thread']
    _description = 'Batch Employee Loan'

    @api.depends('employee_loan_ids','employee_loan_ids.state')
    def _compute_check_loan_paid(self):
        for batch in self:
            if not batch.employee_loan_ids:
                batch_status = 'draft'
            else:
                if any(loan.state == 'draft' for loan in batch.employee_loan_ids):
                    batch_status = 'draft'
                if any(loan.state == 'hr_approval' for loan in batch.employee_loan_ids):
                    batch_status = 'hr_approval'
                if any(loan.state == 'finance_processing' for loan in batch.employee_loan_ids):
                    batch_status = 'finance_processing'
                if any(loan.state == 'approved' for loan in batch.employee_loan_ids):
                    batch_status = 'approved'
                if any(loan.state == 'rejected' for loan in batch.employee_loan_ids):
                    batch_status = 'rejected'
                if any(loan.state == 'cancelled' for loan in batch.employee_loan_ids):
                    batch_status = 'cancelled'
                if all(loan.state == 'done' for loan in batch.employee_loan_ids):
                    batch_status = 'done'
 
            batch.state = batch_status

    @api.depends('employee_loan_ids','employee_loan_ids.state')
    def check_loan_status(self):
        for batch in self:
            if batch.employee_loan_ids:
                if all(loan.state == 'done' for loan in batch.employee_loan_ids):
                    batch.all_loan_paid = True

    name = fields.Char(string="Name", readonly=True, copy=False)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company')
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True, required=True)
    total_loan_amount = fields.Monetary(string="Total Loan Amount",copy=False)
    state = fields.Selection([('draft', 'To Submit'),
                              ('hr_approval', 'HR Approval'),
                              ('finance_processing', 'Finance Processing'),
                              ('approved', 'Confirm'),
                              ('rejected', 'Rejected'),
                              ('cancelled', 'Cancelled'),
                              ('done', 'Done')],
                             string='Status',
                             track_visibility='onchange',
                             compute='_compute_check_loan_paid',store=True)
    batch_loan_journal_id = fields.Many2one('account.journal', string='Journal',copy=False)
    batch_debit_account_id = fields.Many2one('account.account',
                                       string='Loan Payment Account',
                                       copy=False)
    batch_credit_account_id = fields.Many2one('account.account',
                                        string='Loan Installment Account',
                                        copy=False)
    # move_ids = fields.Many2many('account.move', string='Journal Entry',copy=False)
    move_id = fields.Many2one('account.move', string='Journal Entry',copy=False)
    comments = fields.Text('Comments')
    reject_reason = fields.Text('Reject Reason')
    employee_loan_ids = fields.One2many('hr.employee.loan','batch_employee_loan_id',string="Employee Loans")
    all_loan_paid = fields.Boolean(string="Loan Paid",compute="check_loan_status",copy=False,store=True)
    move_name = fields.Char(string="Move name", copy=False)
    
    @api.multi
    def action_open_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', '=', self.move_id.id)]
        action['context'] =  {}
        return action

    @api.constrains('total_loan_amount','batch.employee_loan_ids.loan_amount')
    def check_batch_loan_amount(self):
        for batch in self:
            if batch.total_loan_amount <= 0:
                raise ValidationError(_('Please enter proper batch loan amount.'))
            if batch.employee_loan_ids and batch.total_loan_amount != sum(batch.employee_loan_ids.mapped('loan_amount')):
                raise ValidationError(_('Batch amount and employee loan amount should be same.'))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.employee_loan_ids:
                if all(loan.state != 'draft' for loan in rec.employee_loan_ids):
                    raise Warning(_('You cannot delete Batch Loan Request.'))
                rec.employee_loan_ids.with_context({'from_loan_batch':True}).unlink()
        return super(batch_employee_loan, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_context({'company_id':self.company_id.id}).next_by_code('employee.loan.batch')
        return super(batch_employee_loan, self).create(vals)

    def check_batch_loan_record(self):
        if not self.employee_loan_ids:
            raise ValidationError(_('There is no Employee Loan.!'))

    @api.multi
    def action_submit_for_loan_hr_approval(self):
        self.check_batch_loan_record()
        for emp_loan in self.employee_loan_ids:
            emp_loan.with_context({'from_loan_batch':True}).action_submit_for_loan_hr_approval()

    @api.multi
    def action_submit_loan_cancelled(self):
        self.check_batch_loan_record()
        for emp_loan in self.employee_loan_ids:
            if any(loan_installment.state == 'done' for loan_installment in emp_loan.loan_installment_ids):
                raise ValidationError(_("You can't cancel the Batch Loan because Loan %s installment are paid.!") % (emp_loan.name))
            emp_loan.with_context({'from_loan_batch':True}).action_submit_loan_cancelled()

    @api.multi
    def action_loan_reset_to_draft(self):
        self.check_batch_loan_record()
        for emp_loan in self.employee_loan_ids:
            emp_loan.with_context({'from_loan_batch':True}).action_loan_reset_to_draft()

    @api.multi
    def action_submit_loan_reject(self):
        self.check_batch_loan_record()
        form_view = self.env.ref('bista_employee_loan.hr_employee_loan_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'res_model': 'loan.reject.reason',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    @api.multi
    def action_submit_for_finance_loan_approval(self):
        self.check_batch_loan_record()
        for emp_loan in self.employee_loan_ids:
            emp_loan.with_context({'from_loan_batch':True}).action_submit_for_finance_loan_approval()

    @api.multi
    def action_approved_loan(self):
        self.check_batch_loan_record()
        for emp_loan in self.employee_loan_ids:
            emp_loan.write({'loan_journal_id':self.batch_loan_journal_id.id,
                            'debit_account_id':self.batch_debit_account_id.id,
                            'credit_account_id':self.batch_credit_account_id.id
                            })
            emp_loan.sudo().clear_installment_line()
            if emp_loan.calculate_type == 'auto':
                emp_loan.calculate_loan_amount()
            if emp_loan.calculate_type == 'manual':
                emp_loan.calculate_installment_amount()
            emp_loan.with_context({'from_loan_batch':True}).action_approved_loan()

        self.batch_loan_move_create()

    @api.multi
    def batch_loan_move_create(self):
        '''
        :return: Create First entry of total loan amount.
        '''
        
        move_line_lst = self.prepare_move_lines()
        if move_line_lst:
            move_id = self.env['account.move'].sudo().create({
                'journal_id':self.batch_loan_journal_id.id,
                'company_id':self.company_id.id,
                'date': datetime.today().date(),
                'ref': self.name,
                'line_ids':move_line_lst,
                'name':self.move_name or '/'
            })
            move_id.post()
            move_id.button_cancel()
            for emp_loan in self.employee_loan_ids:
                emp_loan.write({'account_move_id': move_id.id, 'move_name':move_id.name, 'move_ids':[(4, move_id.id)]})
            self.write({'move_id':move_id.id,'move_name':move_id.name})

    def prepare_move_lines(self):
        '''
        :param move: Created move.
        :return: Create Approve loan JE's(First JE's).
        '''
        move_lst = []
        for emp_loan in self.employee_loan_ids:
            debit_entry_dict = {
                'name': emp_loan.name,
                'company_id':self.company_id.id,
                'currency_id':self.company_id.currency_id.id,
                'date_maturity': emp_loan.loan_issuing_date,
                'journal_id':self.batch_loan_journal_id.id,
                'date': datetime.today().date(),
                'partner_id': emp_loan.employee_id.partner_id.id,
                # 'move_id': move.id,
                'debit':emp_loan.loan_amount,
                'account_id':self.batch_credit_account_id.id
            }
            move_lst.append((0, 0, debit_entry_dict))

        credit_entry_dict = {
                'name': self.name,
                'company_id':self.company_id.id,
                'currency_id':self.company_id.currency_id.id,
                'date_maturity': emp_loan.loan_issuing_date,
                'journal_id':self.batch_loan_journal_id.id,
                'date': datetime.today().date(),
                # 'move_id': move.id,
                'credit':self.total_loan_amount,
                'account_id':self.batch_debit_account_id.id
            }
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst
