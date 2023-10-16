# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _


class UpdateMultiLeaveVacationBalance(models.TransientModel):
    _name = 'update.multi.leave.vacation.balance'
    _description = 'Update Multiple Employee Leave/Vacation Balance Wizard'

    update_type = fields.Selection([('leave', 'Leave'),
                                    ('vacation', 'Vacation')], default='leave')
    new_leave_balance = fields.Float('New Leave Balance')
    new_vacation_balance = fields.Float('New Vacation Balance')
    holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type")
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    new_leave_monthly_allowance = fields.Float('New Leave Monthly Allowance')
    new_vacation_monthly_allowance = fields.Float('New Vacation Monthly Allowance')

    @api.onchange('update_type')
    def onchange_update_type(self):
        self.holiday_status_id = False

    def action_confirm(self):
        leave_alloc_obj = self.env['hr.leave.allocation']
        for employee in self.employee_ids:
            leave_bal_line = self.env['employee.leave.balance.by.type'].search([
                ('employee_id', '=', employee.id),
                ('leave_type_id', '=', self.holiday_status_id.id)], limit=1)

            vacation_bal_line = self.env['employee.vacation.balance.by.type'].search([
                ('employee_id', '=', employee.id),
                ('leave_type_id', '=', self.holiday_status_id.id)], limit=1)

            leave_balance = self.new_leave_balance - leave_bal_line.leave_balance
            vacation_balance = self.new_vacation_balance - vacation_bal_line.vacation_balance

            if self.update_type == 'leave':
                leave_alloc_vals = {
                    'name': 'Monthly Leave Allocation for ' + employee.name,
                    'employee_id': employee.id,
                    'holiday_type': 'employee',
                    'allocation_type': 'regular',
                    'leave_type': 'leave',
                    'number_of_days': leave_balance,
                    'holiday_status_id': self.holiday_status_id.id,
                    'type_request_unit': 'hour'
                }
                leave_alloc = leave_alloc_obj.create(leave_alloc_vals)
                leave_alloc.action_approve()
                if leave_bal_line and self.new_leave_monthly_allowance != 0.0:
                    leave_bal_line.write({'leave_monthly_allowance': self.new_leave_monthly_allowance})

            if self.update_type == 'vacation':
                vacation_alloc_vals = {
                    'name': 'Monthly Leave Allocation for ' + employee.name,
                    'employee_id': employee.id,
                    'holiday_type': 'employee',
                    'allocation_type': 'regular',
                    'leave_type': 'vacation',
                    'number_of_days': vacation_balance,
                    'holiday_status_id': self.holiday_status_id.id,
                    'type_request_unit': 'day'
                }
                vacation_alloc = leave_alloc_obj.create(vacation_alloc_vals)
                vacation_alloc.action_approve()
                if vacation_bal_line and self.new_vacation_monthly_allowance != 0.0:
                    vacation_bal_line.write({'vacation_monthly_allowance': self.new_vacation_monthly_allowance})
