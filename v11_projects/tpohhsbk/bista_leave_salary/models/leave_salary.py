# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

import math
import calendar
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LeaveSalary(models.Model):
    _name = "leave.salary"
    _inherit = ['mail.thread']
    _description = "Leave Salary"
    _rec_name = 'employee_id'

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('approve', 'Approve'), ('paid', 'Paid'), ('cancel', 'Cancel')],
                             string='Status', readonly=True,
                             track_visibility='always',
                             default='draft')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='always')
    date = fields.Date('Date', default=fields.date.today())
    leave_accrued = fields.Float('Leave Accrued', digits=(3, 2), compute='compute_leaves_amount', store=True)
    amount_accrued = fields.Float('Amount Accrued', digits=(16, 2), compute='compute_leaves_amount', store=True)
    leave_taken = fields.Float('Leave Taken', digits=(3, 2), track_visibility='always')
    amount_taken = fields.Float('Amount Taken', compute='compute_amount_taken', store=True, track_visibility='always')
    payment_mode = fields.Many2one('account.journal', string='Payment Mode')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
                                      copy=False)
    leave_salary_line_ids = fields.One2many('leave.salary.line', 'leave_salary_id', string="Leave Salary Lines")
    leave_salary_payment_mode = fields.Selection([('direct', 'Direct Payment'), ('salary', 'Salary Payment')], string="Payment Type", default="direct")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    move_name = fields.Char(string="Move Name", copy=False)
    is_accrued = fields.Boolean(string="Is Accrued?", copy=False)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for line in self.leave_salary_line_ids:
            self.write({'leave_salary_line_ids': [(3, line.id)]})

    @api.multi
    def add_leave_salary_lines(self):
        '''
        Add leave request lines from wizard
        :return: wizard
        '''
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Leave Salary Lines'),
            'res_model': 'leave.salary.line.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }
        
    def clear_salary_lines(self):
        self.leave_salary_line_ids.sudo().unlink()
        return True
        
    @api.multi
    def confirm_leave_salary(self):
        leave_salary_line_obj = self.env['leave.salary.line']
        
        if not self.leave_salary_line_ids:
            raise ValidationError('Please add Leave Request Lines.')
        
        if self.env['leave.salary.line'].search([('id', 'in', self.leave_salary_line_ids.ids), ('employee_id', '!=', self.employee_id.id)]):
            raise ValidationError('Please select Leave Request Lines for same employee.')
        
        req_ids = self.leave_salary_line_ids.mapped('leave_request_id')
        exist = leave_salary_line_obj.search([('leave_request_id', 'in', req_ids.ids), ('leave_salary_id', '!=', self.id), ('state', '!=', 'draft')])
        if exist:
            raise ValidationError('Please remove Leave Salary Line which is already Paid or Confirm.')
        
        paid_request = self.leave_salary_line_ids.mapped('leave_request_id').filtered(lambda r: r.leave_salary_paid)
        if paid_request:
            raise ValidationError('Please remove Leave Request which is already Paid.')

        if self.is_accrued:
            if any(not leave_salary_line.leave_request_id.holiday_status_id.accruals for leave_salary_line in self.leave_salary_line_ids):
                raise ValidationError('Please select only accrual type leave request.')

        self.leave_salary_line_ids.write({'state':'confirm'})
        self.write({'state':'confirm',
                    'leave_taken':sum(line.no_of_days for line in self.leave_salary_line_ids)})

    @api.multi
    def approve_leave_salary(self):
        return self.write({'state':'approve'})
        
    @api.multi
    def cancel_leave_salary(self):
        if self.state == 'paid':
            if self.leave_salary_payment_mode == 'salary':
                raise UserError(_('You cannot cancel Leave Salary which is paid from Payslip.'))
            else:
                move_id = self.account_move_id
                if not self.env['ir.module.module'].sudo().search([('name', '=', 'account_cancel'), ('state', '=', 'installed')]):
                    raise UserError(_("Needs To Install \'Cancel Journal Entries\' Module"))
                if move_id.state == 'posted':
                    raise UserError(_("You can't cancel Leave Salary because Journal Entry already posted."))
                if move_id.journal_id.update_posted:
                    move_id.line_ids.remove_move_reconcile()
                    move_id.button_cancel()
                    move_id.with_context({'custom_move':True}).unlink()
                else:
                    raise UserError(_(
                        "Goto Journal -> Adcanced Settings -> "
                        "Allow Cancelling Entries=True "))

        self.leave_salary_line_ids.mapped('leave_request_id').write({'leave_salary_paid':False})
        self.leave_salary_line_ids.write({'state':'draft'})
        return self.write({'state':'cancel'})

    @api.multi
    def reset_leave_salary(self):
        for rec in self:
            rec.leave_salary_line_ids.mapped('leave_request_id').write({'leave_salary_paid':False})
            rec.leave_salary_line_ids.unlink()
            rec.leave_taken = 0
            rec.amount_taken = 0
            
        return self.write({'state':'draft'})
    
    @api.onchange('leave_taken')
    def check_leave_taken(self):
        if self.leave_taken > self.leave_accrued:
            raise ValidationError('Leave taken can not be greater than leave accrued.')

    @api.constrains('leave_taken')
    def leave_taken_change(self):
        if self.is_accrued and self.leave_taken > self.leave_accrued:
            raise ValidationError('Leave taken can not be greater than leave accrued.')

    @api.one
    @api.depends('employee_id')
    def compute_leaves_amount(self):
        """
        Computes all remaining leave, where leave type has accrued true.
        and also compute total salary amount based on those leave.
        also compute pay amount based on trying to leave taken.
        :return:
        """
        
        holidays_add, holidays_removed = self.get_holidays()
        amount_accrued = 0.0
        leave_accrued = 0.0
        removed_days = 0.0
        removed_amount = 0.00
        for holiday in holidays_add:
            amount_accrued += abs(holiday.leave_amount)
            leave_accrued += holiday.number_of_days_temp

        for hl_removed in holidays_removed:
            removed_days += hl_removed.number_of_days_temp
            removed_amount += self.env['leave.salary.line'].sudo().search([('leave_request_id', '=', hl_removed.id)], limit=1).amount

        self.leave_accrued = (leave_accrued - removed_days)
        self.amount_accrued = (amount_accrued - removed_amount)

#     """Done through new leave salary confirmation process"""

    @api.one
    @api.depends('leave_taken')
    def compute_amount_taken(self):
        """
        compute amount for leave taken
        :return:
        """
        self.amount_taken = sum(self.leave_salary_line_ids.mapped('amount'))

    def get_holidays(self):
        """
        search holidays for the selected employee
        :return: allocated leaves to the employee.
        and taken leave that are approved.
        """
        leave_types = self.env['hr.holidays.status'].search([('accruals', '=', True)]).ids
        domain = [
            ('employee_id', '=', self.employee_id.id or False),
            ('state', '=', 'validate'),
            ('company_id', '=', self.company_id.id or False),
            ('holiday_status_id', 'in', leave_types)]
        holidays_add = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'add'),
            ('account_move_id', '!=', False)], order='date_from')
        holidays_removed = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'remove'), ('leave_salary_paid', '=', True)], order='date_from')
        return holidays_add, holidays_removed

    def get_leave_salary(self, date_from, date_to, wages, allocated_leave):
        """
        calculate salary amount for particular leave type
        :param date_from: date_from of particular leave type
        :param date_to: date_to of particular leave type
        :param wages: wages of employee based on contract
        :param allocated_leave: no. of leave allocated in particular time period
        :return: salary amount of total leave allocated for particular time period
        """
        date_from_month = date_from.month
        date_to_month = date_to.month
        leave_salary = 0
        if date_from_month == date_to_month:
            month_days = calendar.monthrange(date_from.year, date_from.month)[1]
            leave_salary = (wages / month_days) * allocated_leave
        elif (date_from_month == 1 and date_from.day == 1) and \
                (date_to_month == 12 and date_to.day == 31):
            if date_from.year % 4 == 0:
                leave_salary = (wages * 12 / 366) * allocated_leave
            else:
                leave_salary = (wages * 12 / 365) * allocated_leave
        return round(leave_salary,2)

    @api.multi
    def pay_leave_salary(self):
        """
        Used to pay salary for leave that employee requests.
        and also create leave for the same days.
        :return:
        """
        self.ensure_one()
        if self.amount_taken <= 0.0:
            raise ValidationError("Amount to pay is not valid.")
        move_lines = []
        holidays_add, holidays_removed = self.get_holidays()
        debit_account_id = False
        expense_account_id = False
        for holiday in holidays_add:
            debit_account_id = holiday.holiday_status_id.leave_salary_journal_id. \
                default_credit_account_id.id
            expense_account_id = holiday.holiday_status_id.expense_account_id.id

        if debit_account_id and expense_account_id:
            debit_exp_vals = {
                'debit': self.amount_taken,
                'credit': 0.0,
                'account_id': debit_account_id,
                'partner_id': self.employee_id.partner_id.id or False,
                'analytic_account_id':self.employee_id.contract_id.analytic_account_id.id,
            }
            move_lines.append((0, 0, debit_exp_vals))

            credit_vals = {
                'debit': 0.0,
                'credit': abs(self.amount_taken),
                'account_id': self.payment_mode.default_credit_account_id.id,
                'partner_id': self.employee_id.partner_id.id,
            }
            move_lines.append((0, 0, credit_vals))
            move_vals = {
                'journal_id': self.payment_mode.id,
                'date': self.date,
                'state': 'draft',
                'line_ids': move_lines,
                'ref': 'Leave Salary Payment',
                'name':self.move_name or '/'
            }
            move = self.env['account.move'].sudo().create(move_vals)
            move.post()
            self.write({'state':'paid','account_move_id':move.id,'move_name':move.name})
            self.leave_salary_line_ids.write({'state':'paid'})
            self.leave_salary_line_ids.mapped('leave_request_id').write({'leave_salary_paid':True})

    def create_leaves(self, holiday_obj):
        """
        create leave of days that employee needs to take salary for
        particular leave days
        :param holiday_obj: object that to be create leave
        :return:
        """
        current_leave_payable = self.leave_taken
        pay_date = datetime.strptime(self.date, DEFAULT_SERVER_DATE_FORMAT)
        date_from = datetime.strptime(self.date, DEFAULT_SERVER_DATE_FORMAT)
        for holiday in holiday_obj:
            if not current_leave_payable > 0:
                break
            holiday_vals = {
                'employee_id': self.employee_id.id or False,
                'holiday_status_id': holiday.holiday_status_id.id or False,
                'company_id': self.company_id.id or False,
                'name': 'Leave Salary',
                'type': 'remove',
                'state': 'validate',
                'date_from': date_from,
            }
            if current_leave_payable >= holiday.number_of_days_temp:
                holiday_vals['number_of_days_temp'] = holiday.number_of_days_temp
                if current_leave_payable > 1:
                    holiday_vals['date_to'] = pay_date + timedelta(days=math.ceil(holiday.number_of_days_temp - 1))
                else:
                    holiday_vals['date_to'] = pay_date
            else:
                holiday_vals['number_of_days_temp'] = current_leave_payable
                if current_leave_payable > 1:
                    holiday_vals['date_to'] = pay_date + timedelta(days=(math.ceil(current_leave_payable) - 1))
                else:
                    holiday_vals['date_to'] = pay_date
            holiday_new = self.env['hr.holidays'].create(holiday_vals)
            pay_date = holiday_new.date_to
            pay_date = datetime.strptime(pay_date, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=1)
            date_from = pay_date
            current_leave_payable = current_leave_payable - holiday_new.number_of_days_temp
        return True

    @api.multi
    def unlink(self):
        for leave_salary in self:
            if leave_salary.state == 'paid':
                raise UserError(_('You cannot delete a paid leave salary.'))
        return super(LeaveSalary, self).unlink()

    @api.multi
    def action_open_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line')
        result = {
            'name': action.name,
            'type': action.type,
            'view_type': 'form',
            'view_mode': 'form',
            'target': action.target,
            'context': self._context,
            'res_id': self.account_move_id.id,
            'res_model': action.res_model,
        }
        return result


class LeaveSalaryLine(models.Model):
    _name = "leave.salary.line"
    _description = "Leave Salary Line"
    
    leave_salary_id = fields.Many2one('leave.salary', string="Leave Salary")
    leave_request_id = fields.Many2one('hr.holidays', string="Leave Request")
    no_of_days = fields.Float(string='No of Days')
    amount = fields.Float(string="Amount")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('paid', 'Paid')], string="State", default="draft")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    employee_id = fields.Many2one('hr.employee', string="Employee")

    @api.onchange('leave_request_id')
    def onchange_leave_request_id(self):
        if self.leave_request_id:
            contract = self.leave_request_id.employee_id.contract_id
            if contract.leave_salary_based == 'basic_salary':
                salary_wages = contract.wage
            elif contract.leave_salary_based == 'gross_salary':
                salary_wages = contract.gross_salary
            elif contract.leave_salary_based == 'basic_accommodation':
                salary_wages = contract.basic_accommodation
            else:
                raise ValidationError("Please Select Leave Salary Based On.")
            
            no_of_days = self.leave_request_id.number_of_days_temp
            amount = (salary_wages / 30) * no_of_days
            
            self.no_of_days = no_of_days
            self.amount = amount
        
        request_ids = []    
        if self.leave_salary_id:
            requests = self.leave_salary_id.leave_salary_line_ids.mapped('leave_request_id').ids
            request_ids = self.env['hr.holidays'].search([('type', '=', 'remove'), ('employee_id', '=', self.leave_salary_id.employee_id.id), ('id', 'not in', requests)]).ids
            
        result = {'domain':{'leave_request_id':[('id', 'in', request_ids)]}}
        
        return result

    @api.model
    def create(self, vals):
        
        if vals.get('leave_request_id', False):
            leave_request = self.env['hr.holidays'].browse(vals.get('leave_request_id'))
            no_of_days, amount = self.days_leave_salary_amount(leave_request)
            date = vals.get('start_date', False)
            if date and isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d')
            month_days = calendar.monthrange(date.year, date.month)[1] or 30

            if vals.get('no_of_days', False):
#                 vals['amount'] = (amount/30) * vals.get('no_of_days')
                vals['amount'] = round((amount / month_days) * vals.get('no_of_days'))
            else:
#                 vals['amount'] = (amount/30) * no_of_days
                vals['amount'] = round((amount / month_days) * no_of_days)
                vals['no_of_days'] = no_of_days

        res = super(LeaveSalaryLine, self).create(vals)
        return res
    
    @api.multi
    def days_leave_salary_amount(self, leave_request):
        contract = leave_request.employee_id.contract_id
        if contract.leave_salary_based == 'basic_salary':
            salary_wages = contract.wage
        elif contract.leave_salary_based == 'gross_salary':
            salary_wages = contract.gross_salary
        elif contract.leave_salary_based == 'basic_accommodation':
            salary_wages = contract.basic_accommodation
        else:
            raise ValidationError("Please Select Leave Salary Based On.")
        
        no_of_days = leave_request.number_of_days_temp
#         amount = (salary_wages/ 30) * no_of_days
        
        return no_of_days, salary_wages
        
