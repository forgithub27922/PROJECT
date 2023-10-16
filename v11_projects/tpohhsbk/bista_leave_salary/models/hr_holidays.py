# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

import calendar
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp


class Holidays(models.Model):
    _inherit = "hr.holidays"

    account_move_id = fields.Many2one('account.move', string="Journal Entry", copy=False)
    leave_accrual_amount = fields.Float(string="Leave Accrual Amount", copy=False)
    move_name = fields.Char(string="Move Name", copy=False)
    leave_salary_paid = fields.Boolean(string="Leave Salary Paid", copy=False)
    move_leave_accrual_amount = fields.Float(string="Total Leave Accrual Amount", copy=False, compute='_compute_move_amount', store=True)
    leave_amount = fields.Float(string="Total Leave Accrual Amount",
                                digits=dp.get_precision('Product Price'))
    is_batch_warning = fields.Boolean(string="Batch Warning")
    increment_wage_amount = fields.Float(string="Increment Wage Amount")
    batch_id = fields.Many2one('leave.allocation.batch', string="Batch", copy=False)

    @api.onchange('employee_id', 'date_from', 'date_to', 'number_of_days_temp')
    def onchange_leave_amount(self):
        if self._context.get('from_batch_calculation') and self.employee_id and self.date_from and self.date_to and self.number_of_days_temp:
            contract = self.employee_id.contract_id
            self.leave_amount = 0.00
            if not self.company_id:
                self.company_id = self.env.user.company_id.id
            if not contract:
                return
            if contract and not contract.is_cal_salary_accrual:
                return
            if contract.leave_salary_based == 'basic_salary':
                salary_wages = contract.wage
            elif contract.leave_salary_based == 'gross_salary':
                salary_wages = contract.gross_salary
            elif contract.leave_salary_based == 'basic_accommodation':
                salary_wages = contract.basic_accommodation
            else:
                raise ValidationError("Please Select Leave Salary Based On.")

            no_of_days = self.number_of_days_temp
            date = datetime.strptime(self.date_from, '%Y-%m-%d')
            date_to = datetime.strptime(self.date_to, '%Y-%m-%d')
            month_days = calendar.monthrange(date.year, date.month)[1] or 30
            # amount = ((salary_wages / month_days) * self.number_of_days_temp)
            # self.leave_amount = amount
            amount = self.get_leave_salary(date, date_to, salary_wages, no_of_days)
            self.leave_amount = amount

    @api.multi
    def _track_subtype(self, init_values):
        '''
            Override Method to Skip email send for leave allocation and leave request.
        '''
        if 'state' in init_values and self.state in ['validate', 'validate1', 'confirm', 'refuse']:
            return
        return super(Holidays, self)._track_subtype(init_values)

    @api.multi
    @api.depends('account_move_id', 'state')
    def _compute_move_amount(self):
        for holiday in self:
            if holiday.type == 'add':
                holiday.move_leave_accrual_amount = holiday.account_move_id.amount

    @api.multi
    def action_refuse(self):
        for holiday in self:
            if holiday.type == 'add' and not self._context.get('from_batch'):
                move_id = holiday.account_move_id.sudo()
                if move_id.state == 'posted':
                    raise ValidationError(_("You can't cancel Leave Allocation because Journal Entry already posted.!"))

                if holiday.batch_id and move_id:
                    if not holiday.is_batch_warning:
                        return{
                            'name':'Leave Refuse Confirmation',
                            'type':'ir.actions.act_window',
                            'view_mode':'form',
                            'view_type':'form',
                            'res_model':'holiday.batch.refuse',
                            'view_id':self.env.ref('bista_leave_salary.holiday_batch_refuse_form_view').id,
                            'context':{'default_holidays_id':holiday.id,
                                       'default_name':" * Refuse Leave will refuse batch '%s' leave allocation." % (holiday.batch_id.name),
                                       'default_batch_id':holiday.batch_id.id},
                            'target':'new'
                            }
                    else:
                        holiday.batch_id.with_context({'holiday_id':holiday.id}).do_cancel()
                        holiday.write({'leave_amount':0, 'is_batch_warning':True, 'leave_accrual_amount':0.00})
                else:
                    move_id.button_cancel()
                    move_id.line_ids.remove_move_reconcile()
                    move_id.with_context({'custom_move':True}).unlink()
                    holiday.leave_amount = 0.00
                    if holiday.increment_wage_amount > 0:
                        holiday.employee_id.contract_id.is_increment_paid = False
                        holiday.increment_wage_amount = 0.00
            else:
                if holiday.increment_wage_amount > 0:
                    holiday.employee_id.contract_id.is_increment_paid = False
                holiday.increment_wage_amount = 0.00

        return super(Holidays, self).action_refuse()

    @api.multi
    def get_journal_entry(self):
        '''
        Get Linked Journal Entry
        :return:
        '''
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', self.account_move_id.ids)],
            'res_id': self.account_move_id.ids,
            'target': 'current',
        }

    @api.multi
    def action_approve(self):
        """
        while single validating leave approval first create journal entry and
        then calls parent method
        :return:
        """
        for holiday in self:
            if not holiday.employee_id.contract_id:
                raise ValidationError("Contract not in Running state.")
            if not holiday.double_validation and holiday.employee_id.contract_id and not self._context.get('from_batch'):
                if holiday.holiday_status_id.accruals:
                    if holiday.type == 'add':
                        if not holiday.batch_id:
                            holiday.create_move(holiday)
                        else:
                            raise UserError(_("You can't Approve leave Allocation which are created from Batch '%s' Leave Allocation.") % (holiday.batch_id.name))
                    else:
                        holiday.get_leave_request_amount()
            if holiday.increment_wage_amount > 0:
                holiday.employee_id.contract_id.is_increment_paid = True
        super(Holidays, self).action_approve()

    @api.multi
    def action_draft(self):
        for holiday in self:
            if holiday.holiday_status_id.accruals and holiday.type == 'add':
                if holiday.batch_id and not self._context.get('from_batch'):
                    raise UserError(_("You can't Reset To Draft leave Allocation which are created from Batch '%s' Leave Allocation.") % (holiday.batch_id.name))
            return super(Holidays, self).action_draft()

    @api.multi
    def action_confirm(self):
        for holiday in self:
            if holiday.holiday_status_id.accruals and holiday.type == 'add' and not self._context.get('from_batch'):
                if holiday.batch_id:
                    raise UserError(_("You can't Confirm leave Allocation which are created from Batch '%s' Leave Allocation.") % (holiday.batch_id.name))
            return super(Holidays, self).action_confirm()

    @api.multi
    def action_validate(self):
        """
        while double validating leave approval first create journal entry and
        then calls parent method
        :return:
        """
        for holiday in self:
            if not holiday.employee_id.contract_id:
                raise ValidationError("Contract not in Running state.")
            if holiday.double_validation and holiday.employee_id.contract_id and not self._context.get('from_batch'):
                if holiday.holiday_status_id.accruals:
                    if holiday.type == 'add':
                        if not holiday.batch_id:
                            holiday.create_move(holiday)
                        else:
                            raise UserError(_("You can't Approve leave Allocation which are created from Batch '%s' Leave Allocation.") % (holiday.batch_id.name))
                    else:
                        holiday.get_leave_request_amount()

        return super(Holidays, self).action_validate()

    def get_leave_request_amount(self):
        contract = self.employee_id.contract_id
        if not contract:
            return
        if contract and not contract.is_cal_salary_accrual:
            return 
        if self.is_leave_adjustment or self.lapse_leave_id:
            return
        if contract.leave_salary_based == 'basic_salary':
            salary_wages = contract.wage
        elif contract.leave_salary_based == 'gross_salary':
            salary_wages = contract.gross_salary
        elif contract.leave_salary_based == 'basic_accommodation':
            salary_wages = contract.basic_accommodation
        else:
            raise ValidationError("Please Select Leave Salary Based On.")

        date = self.date_from or datetime.today().date().strftime('%Y-%m-%d')
        date = datetime.strptime(date, '%Y-%m-%d')
        month_days = calendar.monthrange(date.year, date.month)[1] or 30
        self.leave_amount = round((salary_wages / month_days) * self.number_of_days_temp,2) * -1

    def create_move(self, holiday):
        """
        creates journal entry as leave salary while validating allocated leave
        :param holiday: object that is trying to validate
        :return:
        """
        salary_wages = 0
        leave_salary = 0
        contract = holiday.employee_id.contract_id
        if contract and not contract.is_cal_salary_accrual:
            return
        if not holiday.leave_accrual_amount > 0:
            if contract.leave_salary_based == 'basic_salary':
                salary_wages = contract.wage
            elif contract.leave_salary_based == 'gross_salary':
                salary_wages = contract.gross_salary
            elif contract.leave_salary_based == 'basic_accommodation':
                salary_wages = contract.basic_accommodation
            else:
                raise ValidationError("Please Select Leave Salary Based On.")
            leave_salary = self.get_leave_salary(datetime.strptime(holiday.date_from, '%Y-%m-%d'),
                                                 datetime.strptime(holiday.date_to, '%Y-%m-%d'),
                                                 salary_wages, holiday.number_of_days_temp)
        else :
            leave_salary = holiday.leave_accrual_amount * holiday.number_of_days_temp
        if not holiday.name:
            raise ValidationError("Please Enter the Description.")
        debit_vals = {
            'name': holiday.name,
            'debit': abs(leave_salary),
            'credit': 0.0,
            'analytic_account_id':contract.analytic_account_id.id,
            'account_id': holiday.holiday_status_id.expense_account_id.id or False,
            'partner_id': holiday.employee_id.partner_id.id or False,
        }
        credit_vals = {
            'debit': 0.0,
            'credit': abs(leave_salary),
            'account_id': holiday.holiday_status_id.leave_salary_journal_id. \
                              default_credit_account_id.id or False,
            'partner_id': holiday.employee_id.partner_id.id or False,
            'name': holiday.name
        }
        vals = {
            'journal_id': holiday.holiday_status_id.leave_salary_journal_id.id,
            'date': holiday.date_to,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Leave Salary Accrual'
        }
        if holiday.move_name:   
            vals['name'] = holiday.move_name

        move = self.env['account.move'].sudo().create(vals)
        move.post()
        move.button_cancel()
        self.write({'account_move_id' : move.id, 'move_name':move.name, 'leave_amount':leave_salary})

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

#         domain = [('employee_id', '=', self.employee_id.id), ('type', '=', 'add') ,
#                   ('state', '=', 'validate'),
#                   ('is_pro_rata_leave', '=', True), ('id', '!=', self.id)]
# 
#         previous_month_holiday = self.search(domain, limit=1)

#         if previois_month_holiday:
#             previois_date_from = datetime.strptime(previois_month_holiday.date_from, '%Y-%m-%d')
#             previois_amount = previois_month_holiday.leave_amount
#             month_days = calendar.monthrange(previois_date_from.year, previois_date_from.month)[1]
#             previois_month_day_amount = (previois_amount / previois_month_holiday.number_of_days_temp)
#             previois_month_wage_amount = round(previois_month_day_amount * month_days)

        current_month_days = calendar.monthrange(date_from.year, date_from.month)[1]

        previous_month_wage_amount = self.employee_id.contract_id.old_salary_amount
        if previous_month_wage_amount > 0 and not self.employee_id.contract_id.is_increment_paid and wages != previous_month_wage_amount:
            holidays_add, holidays_removed = self.get_holidays()
            leave_allocation_amount = sum(holidays_add.mapped('leave_amount'))
            leave_allocation_no_of_days = sum(holidays_add.mapped('number_of_days_temp'))
            leave_request_amount = abs(sum(holidays_removed.mapped('leave_amount')))
            leave_request_no_of_days = sum(holidays_removed.mapped('number_of_days_temp'))
            leave_encash_amount = 0.00

            for holiday  in holidays_removed.filtered(lambda l:l.encashment_id):
                leave_encash_amount += sum(holiday.encashment_id.mapped('move_ids.amount'))

            diff_days = abs(leave_allocation_no_of_days - leave_request_no_of_days)
#                 diff_amount = abs(leave_allocation_amount - (leave_request_amount - leave_encash_amount))
            diff_amount = abs(leave_allocation_amount - leave_request_amount)
            wage_amount = (wages / current_month_days)

            new_wage_amount = (diff_days * wage_amount)
            final_diff_amount = abs(new_wage_amount - diff_amount)
            if final_diff_amount > 0 :
                self.increment_wage_amount = final_diff_amount
                leave_salary += final_diff_amount
                self.employee_id.contract_id.is_increment_paid = True
#                     self.create_increment_wage_amount_move(final_diff_amount)
        return round(leave_salary,2)

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
            ('company_id', '=', self.company_id.id),
            ('holiday_status_id', 'in', leave_types)]
        holidays_add = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'add'),
            ('account_move_id', '!=', False)], order='date_from')
        holidays_removed = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'remove')], order='date_from')
        return holidays_add, holidays_removed

    def create_increment_wage_amount_move(self, amount):
        salary_wages = 0
        leave_salary = 0
        
        move_line_lst = []
        debit_vals = {
                    'name': 'Accrual Adjustment Entry',
                    'debit': abs(amount),
                    'account_id': self.holiday_status_id.expense_account_id.id,
                    }
        credit_vals = {
            'name': 'Accrual Adjustment Entry',
            'credit': abs(amount),
            'account_id': self.holiday_status_id.leave_salary_journal_id. \
                              default_credit_account_id.id or False,
        }
        vals = {
            'journal_id': self.holiday_status_id.leave_salary_journal_id.id,
            'date': datetime.now().date(),
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Leave Accrual Adjustment',
            'company_id':self.company_id.id
        }
        move = self.env['account.move'].sudo().create(vals)


class HrHolidayStatus(models.Model):
    _inherit = 'hr.holidays.status'

    accruals = fields.Boolean('Accruals')
    expense_account_id = fields.Many2one('account.account', 'Expense Account')
    leave_salary_journal_id = fields.Many2one('account.journal', 'Leave Salary Journal')


class holiday_batch_refuse(models.TransientModel):
    _name = 'holiday.batch.refuse'

    name = fields.Char(string="Warning message")
    holidays_id = fields.Many2one('hr.holidays', string="Holidays")
    batch_id = fields.Many2one('leave.allocation.batch', string="Batch")

    @api.multi
    def refuse_batch_leave(self):
        for holiday_id in self.batch_id.holiday_batch_ids:
            holiday_id.is_batch_warning = True
