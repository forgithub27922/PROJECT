import calendar
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class LeaveEncashmentPayment(models.TransientModel):
    _name = "leave.encashment.payment.wizard"
    
    journal_id = fields.Many2one('account.journal', string="Payment Journal")
    payment_date = fields.Date(string="Payment Date")
    amount = fields.Float(string="Payment Amount")
    leave_encashment_id = fields.Many2one("leave.encashment", string="Leave Encashment")

    @api.multi
    def pay_leave_salary(self):
        """
        Used to pay leave encashment for employee
        :return:
        """
        self.ensure_one()
        if self.amount <= 0.0:
            raise ValidationError("Amount to pay is not valid.")

        debit_account_id = self.leave_encashment_id.holiday_status_id.leave_salary_journal_id.default_credit_account_id.id
        credit_account_id = self.journal_id.default_credit_account_id.id
        partner_id = self.leave_encashment_id.employee_id.partner_id.id

        debit_vals = {
            'debit': abs(self.amount),
            'credit': 0.0,
            'account_id': debit_account_id or False,
            'partner_id': partner_id or False,
        }
        credit_vals = {
            'debit': 0.0,
            'credit': abs(self.amount),
            'account_id': credit_account_id or False,
            'partner_id': partner_id or False,
        }
        move_vals = {
            'journal_id': self.journal_id.id or False,
            'date': self.payment_date,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Leave Salary Payment'
        }
        move = self.env['account.move'].sudo(self.env.user.id).create(move_vals)
        self.leave_encashment_id.write({'move_ids':[(4, move.id)], 'state':'paid'})

        # lapse_leave = self.env['hr.holidays'].search([('encashment_id', '=', self.leave_encashment_id.id)])
        # if lapse_leave:
            # diff_amount = abs((abs(lapse_leave.leave_amount) - self.amount))
            
            # Below Code is generate difference of lapse leave and encash leave.
            # based on contract salary type it will get the amount.

            # diff_days = abs(self.leave_encashment_id.leaves_to_lapse - self.leave_encashment_id.days_to_encash)
            # if diff_days:
            #     contract_id = self.leave_encashment_id.employee_id.contract_id
            #     if not contract_id:
            #         raise ValidationError("Employee contract is not in running state.")
            #     if contract_id.leave_salary_based:
            #         wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
            #         'basic_accommodation':'basic_accommodation'}
            #         contract_type = wage_dict[contract_id.leave_salary_based]
            #         contract_amount = contract_id[contract_type]
            #         encash_date = datetime.strptime(self.leave_encashment_id.encash_date,'%Y-%m-%d').date()
            #         days = calendar.monthrange(encash_date.year, encash_date.month)[1]
            #         each_day_amount = contract_amount / days
            #         final_amount = each_day_amount * diff_days
            #         diff_amount += final_amount

            # if diff_amount:
            #     debit_vals = {
            #     'debit': diff_amount,
            #     'credit': 0.0,
            #     'account_id': debit_account_id,
            #     'partner_id': partner_id,
            #     'name':'Leave Salary Adjustment Entry'
            #     }
            #     credit_vals = {
            #         'debit': 0.0,
            #         'credit': diff_amount,
            #         'account_id': self.leave_encashment_id.holiday_status_id.expense_account_id.id,
            #         'partner_id': partner_id,
            #         'analytic_account_id':lapse_leave.employee_id.contract_id.analytic_account_id.id,
            #         'name':'Leave Salary Adjustment Entry'
            #     }
            #     move_vals = {
            #         'journal_id': self.journal_id.id,
            #         'date': self.payment_date,
            #         'state': 'draft',
            #         'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            #         'ref': 'Leave Salary Adjustment Entry'
            #     }
            #     move = self.env['account.move'].sudo(self.env.user.id).create(move_vals)
            #     self.leave_encashment_id.write({'move_ids':[(4, move.id)]})

            # lapse_leave.write({'encash_amount': self.amount * -1})
        return True
