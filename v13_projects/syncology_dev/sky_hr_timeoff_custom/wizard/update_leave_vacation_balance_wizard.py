# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UpdateLeaveVacationBalance(models.TransientModel):
    _name = 'update.leave.vacation.balance'
    _description = 'Update Leave/Vacation Balance Wizard'

    update_type = fields.Selection([('leave', 'Leave'),
                                    ('vacation', 'Vacation')], default='leave')
    current_leave_balance = fields.Float('Current Leave Balance')
    new_leave_balance = fields.Float('New Leave Balance')
    current_vacation_balance = fields.Float('Current Vacation Balance')
    new_vacation_balance = fields.Float('New Vacation Balance')
    current_leave_monthly_allowance = fields.Float('Current Leave Monthly Allowance')
    new_leave_monthly_allowance = fields.Float('New Leave Monthly Allowance')
    current_vacation_monthly_allowance = fields.Float('Current Vacation Monthly Allowance')
    new_vacation_monthly_allowance = fields.Float('New Vacation Monthly Allowance')
    holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type")

    @api.onchange('update_type')
    def onchange_update_type(self):
        self.holiday_status_id = False

    @api.onchange('holiday_status_id')
    def onchange_leave_type(self):
        """ This Method will update wizard Cureent Leave/Vacation Balance and Leave/Vacation Monthly Allowance
        from Employee Vacation and Leave Balance Table """
        if self.holiday_status_id:
            current_id = self.env.context.get('active_id')
            employee = self.env['hr.employee'].browse(current_id)
            if self.update_type == 'leave':
                emp_leave_bal = self.env['employee.leave.balance.by.type'].search([
                    ('employee_id', '=', employee.id),
                    ('leave_type_id', '=', self.holiday_status_id.id)], limit=1)
                if emp_leave_bal:
                    self.current_leave_monthly_allowance = emp_leave_bal.leave_monthly_allowance
                    self.current_leave_balance = emp_leave_bal.leave_balance
                    self.new_leave_balance = emp_leave_bal.leave_balance
                    self.new_leave_monthly_allowance = emp_leave_bal.leave_monthly_allowance
            if self.update_type == 'vacation':
                emp_vaca_bal = self.env['employee.vacation.balance.by.type'].search([
                    ('employee_id', '=', employee.id), ('leave_type_id', '=', self.holiday_status_id.id,)], limit=1)
                if emp_vaca_bal:
                    self.current_vacation_monthly_allowance = emp_vaca_bal.vacation_monthly_allowance
                    self.current_vacation_balance = emp_vaca_bal.vacation_balance
                    self.new_vacation_balance = emp_vaca_bal.vacation_balance
                    self.new_vacation_monthly_allowance = emp_vaca_bal.vacation_monthly_allowance

    def action_confirm(self):
        """
        On confirm, create Leave/Vacation Allocation of new leave/vacation balance - current balance
        and Update Leave/Vacation Monthly Allowance
        :return:
        """
        leave_alloc_obj = self.env['hr.leave.allocation']
        vac_bal_by_type_obj = self.env['employee.vacation.balance.by.type']
        lv_bal_by_type_obj = self.env['employee.leave.balance.by.type']
        current_id = self.env.context.get('active_id')
        employee = self.env['hr.employee'].browse(current_id)

        leave_bal_line = lv_bal_by_type_obj.search([
            ('employee_id', '=', employee.id),
            ('leave_type_id', '=', self.holiday_status_id.id)
        ], limit=1)

        vacation_bal_line = vac_bal_by_type_obj.search([
            ('employee_id', '=', employee.id),
            ('leave_type_id', '=', self.holiday_status_id.id)
        ], limit=1)

        if not vacation_bal_line.ids:
            vacation_bal_line = vac_bal_by_type_obj.create({
                'employee_id': employee.id,
                'leave_type_id': self.holiday_status_id.id
            })

        if not leave_bal_line.ids:
            leave_bal_line = lv_bal_by_type_obj.create({
                'employee_id': employee.id,
                'leave_type_id': self.holiday_status_id.id
            })

        leave_balance = self.new_leave_balance - leave_bal_line.leave_balance
        vacation_balance = self.new_vacation_balance - vacation_bal_line.vacation_balance

        if self.new_leave_monthly_allowance > self.new_leave_balance:
            raise ValidationError(_("New leave monthly allowance should be less than leave balance!"))

        if self.new_vacation_monthly_allowance > self.new_vacation_balance:
            raise ValidationError(_(
                "New vacation monthly allowance should be less than current vacation balance!"))

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
            if leave_alloc.state == 'validate1':
                leave_alloc.action_validate()
            if leave_bal_line:
                leave_bal_line.write({'leave_monthly_allowance': self.new_leave_monthly_allowance})
            # employee.write({'leave_monthly_allowance': self.new_leave_monthly_allowance})

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
            if vacation_alloc.state == 'validate1':
                vacation_alloc.action_validate()
            if vacation_bal_line:
                vacation_bal_line.write({'vacation_monthly_allowance': self.new_vacation_monthly_allowance})
