# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math

class GratuityAdvancePayment(models.TransientModel):
    _name = "eos.fnf.payment.wizard"
    
    journal_id = fields.Many2one('account.journal',string="Payment Journal")
    date = fields.Date(string="Payment Date")
    ref = fields.Char(string="Reference")
    check_no = fields.Char(string="Check Number")
    journal_type = fields.Selection(related='journal_id.type',sring="Journal Type")

    @api.multi
    def pay_eos_fnf(self):
        """
        Used to pay eos fnf for employee
        :return:
        """
        self.ensure_one()
        ctx = self._context.copy()
        active_model = ctx.get('active_model')
        active_id = ctx.get('active_id')
        global move_lines
        move_lines = []

        emp_exit_request_id = self.env[active_model].browse(active_id)
        
        if any(not special_allwance.allowance_expense_account_id for special_allwance in emp_exit_request_id.spl_allowance_ids):
            raise ValidationError("Please Configure Spacial Allowance Account.")

        if any(not other_deduction.deduction_account_id for other_deduction in emp_exit_request_id.other_deduct_ids):
            raise ValidationError("Please Configure Other Deduction Account.")

        if emp_exit_request_id.employee_asset_ids and \
            not emp_exit_request_id.asset_penalty_account_id:
            raise ValidationError("Please Configure Asset Penalty Account.")

        if not self.journal_id.default_credit_account_id:
            raise ValidationError(_('Please Configure %s Journal Credit/Debit Account.') % (self.journal_id.name))

        expenses_type_acc_id = self.env.ref('account.data_account_type_expenses')
        analytic_account_id = emp_exit_request_id.employee_id.contract_id.analytic_account_id

        ff_amount = emp_exit_request_id.final_ff_amount
        move_vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': self.ref,
            'narration':emp_exit_request_id.reason,
            'check_number_char':self.check_no
        }
        move_id = self.env['account.move'].sudo().create(move_vals)

        # asset penalties
        asset_penalty_total = sum(asset.penalties for asset in emp_exit_request_id.employee_asset_ids)
        if asset_penalty_total:
            asset_penalty_vals = {
                'debit': 0.0,
                'credit': asset_penalty_total,
                'account_id': emp_exit_request_id.asset_penalty_account_id.id,
                'analytic_account_id':analytic_account_id if emp_exit_request_id.asset_penalty_account_id.user_type_id.id == expenses_type_acc_id.id else False,
                'name': 'Asset Penalty'
            }
            move_lines.append((0, 0, asset_penalty_vals))

        # Loan
        for loan in emp_exit_request_id.loan_ids:
            if not loan.loan_journal_id.default_credit_account_id:
                raise ValidationError(_('Please Configure %s Journal Credit/Debit Account.') % (loan.loan_journal_id.name))

            move_lines.append((0, 0, {
                'debit': 0.0,
                'credit': loan.remaining_installments_total_amount,
                'account_id': loan.loan_journal_id.default_credit_account_id.id,
                'name': 'Loan' + loan.name + 'Payable'
            }))
            for installment in loan.loan_installment_ids:
                installment.write({'state': 'done', 
                                    'paid_date': fields.date.today(),'paid_amount': installment.amount})
            if all(loan_statement.state == 'done' for loan_statement in loan.loan_installment_ids):
                loan.write({'state': 'done'})

            loan.write({'move_ids':[(4, move_id.id)]})

        # Payslip Data Prepare
        for payslip in emp_exit_request_id.slip_ids:
            if not payslip.journal_id.default_debit_account_id:
                raise ValidationError(_('Please Configure %s Journal Credit/Debit Account.') % (payslip.journal_id.name))

            if payslip.state == 'draft':
                payslip.action_payslip_done()

            move_lines.append((0,0,{
                'debit': payslip.net_amount,
                'credit': 0.0,
                'account_id': payslip.journal_id.default_debit_account_id.id,
                'analytic_account_id':analytic_account_id.id if payslip.journal_id.default_debit_account_id.user_type_id.id == expenses_type_acc_id.id else False,
                'name': payslip.name or payslip.number
            }))
        
            payslip.write({'is_paid': True, 'state': 'paid',
                               'employee_payment_journal_id':self.journal_id.id,
                               'account_move_id': move_id.id})

        # Leave Encahsment Prepare Journal Entry Data
        self.create_leave_adjustment(emp_exit_request_id)

        # Spacial Allowance
        for sp_allowance in emp_exit_request_id.spl_allowance_ids.filtered(lambda l:l.base_crncy_amount):
            move_lines.append((0, 0, {
            'debit': sp_allowance.base_crncy_amount,
            'credit': 0.0,
            'analytic_account_id':analytic_account_id.id if sp_allowance.allowance_expense_account_id.user_type_id.id == expenses_type_acc_id.id else False,
            'account_id': sp_allowance.allowance_expense_account_id.id,
            'name': sp_allowance.description
            }))

        
        # Other Deduction
        for other_deduction in emp_exit_request_id.other_deduct_ids.filtered(lambda l:l.base_crncy_amount):
            move_lines.append((0, 0, {
            'debit': 0.0,
            'credit': other_deduction.base_crncy_amount,
            'account_id': other_deduction.deduction_account_id.id,
            'name': other_deduction.description,
            'analytic_account_id':analytic_account_id.id if other_deduction.deduction_account_id.user_type_id.id == expenses_type_acc_id.id else False,
        }))
        
        # Gratuity
        if emp_exit_request_id.gtt_max_payabel:
            if not emp_exit_request_id.company_id.gratuity_journal_id:
                raise ValidationError(_('Please Configure Gratuity Journal for %s Company.') % (emp_exit_request_id.company_id.name))

            if not emp_exit_request_id.company_id.gratuity_journal_id.default_debit_account_id:
                raise ValidationError(_('Please Configure %s Journal Credit/Debit Account.') % (emp_exit_request_id.company_id.gratuity_journal_id.name))

            if not emp_exit_request_id.company_id.gratuity_account_id:
                raise ValidationError(_('Please Configure Gratuity Expense Account for %s Company.') % (emp_exit_request_id.company_id.name))

            move_lines.append((0, 0, {
                'debit': emp_exit_request_id.gtt_max_payabel,
                'credit': 0.0,
                'account_id': emp_exit_request_id.company_id.gratuity_account_id.id,
                'name': 'Gratuity',
                'analytic_account_id':analytic_account_id.id if emp_exit_request_id.company_id.gratuity_account_id.user_type_id.id == expenses_type_acc_id.id else False,
            }))

        move_lines.append((0, 0, {
            'debit': 0.0,
            'credit': ff_amount,
            'account_id': self.journal_id.default_credit_account_id.id,
            'name': 'Full & Final Amount',
            'partner_id':emp_exit_request_id.employee_id.partner_id.id
        }))
        move_id.write({'line_ids':move_lines})
        emp_exit_request_id.write({'state': 'paid','account_move_id':move_id.id})

    def create_leave_adjustment(self,emp_exit_request_id):
        '''
            Create Leave Encashment for the employee instead of directly Lapse Leave.
            if employee experies < 1 Year than leave encahsment is 2.0 based on
            leave allocation  month otherwise take normal leave encashment.
        '''
        leave_encashment_obj = self.env['leave.encashment']
        encashment_payment_wizard_obj = self.env['leave.encashment.payment.wizard']
        
        for leave in emp_exit_request_id.salary_ids:
            move_lines.append((0,0,{
                'debit': leave.leave_salary_amount,
                'credit': 0.0,
                'account_id': leave.leave_type_id.expense_account_id.id,
                'analytic_account_id':emp_exit_request_id.employee_id.contract_id.analytic_account_id.id,
                'name': leave.leave_type_id.name + '- ' + 'Salary Payable',
            }))
            current_experience = emp_exit_request_id.employee_id.current_experience
            vals = {
                    'encash_date':emp_exit_request_id.relieve_date,'employee_id':emp_exit_request_id.employee_id.id,
                    'holiday_status_id':leave.leave_type_id.id,'type':'lapse_and_encash',
                    'leaves_to_lapse':leave.leave_balance,'days_to_encash':leave.leave_balance,
                    'leave_encashment_payment_mode':'direct','company_id':emp_exit_request_id.company_id.id,
                    'eos_fnf_id':emp_exit_request_id.id
                    }

            '''
                Need to Change the Code for as per discussion with Anup Sir.
                if employee experience < 1 leave balance should be encashed  * 2.
                For Ex: EMP 101 have Allocation 25 Leave in 10 month than 
                leave encashed 10 month  * 2  = 20 leave.
            '''
            if current_experience < 1:
                get_leave_day = self.get_leave_allocation(leave,emp_exit_request_id)
                vals['days_to_encash'] = (get_leave_day * 2)

            leave_encashment_id = leave_encashment_obj.create(vals)
            leave_encashment_id.with_context({'from_eos':True}).action_confirm()
            leave_encashment_id.with_context({'from_eos':True}).action_approved()

            encashment_payment_wizard_obj = encashment_payment_wizard_obj.create({'amount':leave_encashment_id.encash_amount,
                                                  'leave_encashment_id':leave_encashment_id.id,
                                                  'payment_date':leave_encashment_id.encash_date,
                                                  'journal_id':self.journal_id.id
                                                  })
            encashment_payment_wizard_obj.pay_leave_salary()
            leave_encashment_obj |= leave_encashment_id

        # holidays_obj = self.env['hr.holidays'].sudo()
        # for leave in emp_exit_request_id.salary_ids:
            # move_lines.append((0,0,{
            #     'debit': leave.leave_salary_amount,
            #     'credit': 0.0,
            #     'account_id': leave.leave_type_id.expense_account_id.id,
            #     'analytic_account_id':emp_exit_request_id.employee_id.contract_id.analytic_account_id.id,
            #     'name': leave.leave_type_id.name + '- ' + 'Salary Payable',
            # }))
        #     leave_vals = {
        #             'name': 'Lapse Leave Created',
        #             'state': 'confirm',
        #             'type': 'remove',
        #             'holiday_status_id': leave.leave_type_id.id,
        #             'employee_id': emp_exit_request_id.employee_id.id,
        #             'number_of_days_temp': leave.leave_balance,
        #             'department_id':emp_exit_request_id.employee_id.department_id.id,
        #             'lapse_leave': True,
        #             'is_leave_adjustment':True,
        #             'date_from': self.date,
        #             'date_to': self.date,
        #             'company_id':emp_exit_request_id.company_id.id,
        #             'leave_amount':-leave.leave_salary_amount
        #         }
        #     hr_holiday_id = holidays_obj.create(leave_vals)
        #     hr_holiday_id.action_approve()
        #     if hr_holiday_id.holiday_status_id.double_validation:
        #         hr_holiday_id.action_validate()


    def get_leave_allocation(self,leave,emp_exit_request_id):
        '''
            get leave allocation total count. 
        '''
        # ('is_pro_rata_leave','=',True)
        domain = [('employee_id', '=', emp_exit_request_id.employee_id.id or False),
                  ('state', '=', 'validate'),('type', '=', 'add'),
                  ('company_id','=',emp_exit_request_id.company_id.id),
                  ('holiday_status_id', '=', leave.leave_type_id.id)]
        holidays_add = self.env['hr.holidays'].search_count(domain)
        return holidays_add