# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
import math


class EmployeeLeaveBalanceByType(models.Model):
    _name = 'employee.leave.balance.by.type'
    _description = 'Employee Leave Balance By Type'

    def _cal_leave_bal_by_type(self):
        """This will calculate leave balance of Employee by Leave type
        (allocated leave - leave request for particular leave type)"""
        leave_alloc_obj = self.env['hr.leave.allocation']
        leave_request_obj = self.env['hr.leave']
        for rec in self:
            leave_allocation = leave_alloc_obj.search([('employee_id', '=', rec.employee_id.id),
                                                       ('state', 'in', ('validate', 'validate1')),
                                                       ('leave_type', '=', 'leave'),
                                                       ('holiday_status_id', '=', rec.leave_type_id.id)])
            leave_allocation_days = sum(leave_allocation.mapped('number_of_hours_display'))
            leaves = leave_request_obj.search([('employee_id', '=', rec.employee_id.id),
                                               ('state', 'in', ('validate', 'validate1')),
                                               ('leave_type', '=', 'leave'),
                                               ('holiday_status_id', '=', rec.leave_type_id.id)])
            leave_hours = 0.0
            for leave in leaves:
                leave_hours += math.ceil(leave.end_time - leave.start_time)
            rec.leave_balance = leave_allocation_days - leave_hours

    employee_id = fields.Many2one('hr.employee', string='Employee')
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    leave_monthly_allowance = fields.Float('Monthly Allowance')
    leave_balance = fields.Float('Leave Balance', compute='_cal_leave_bal_by_type')


class EmployeeVacationBalanceByType(models.Model):
    _name = 'employee.vacation.balance.by.type'
    _description = 'Employee Vacation Balance By Type'

    def _cal_vaca_bal_by_type(self):
        """This will calculate vacation balance of Employee by Leave type
               (allocated leave - leave request for particular leave type)"""
        leave_alloc_obj = self.env['hr.leave.allocation']
        leave_request_obj = self.env['hr.leave']
        for rec in self:
            vacation_allocation = leave_alloc_obj.search([('employee_id', '=', rec.employee_id.id),
                                                          ('state', 'in', ('validate', 'validate1')),
                                                          ('leave_type', '=', 'vacation'),
                                                          ('holiday_status_id', '=', rec.leave_type_id.id)])
            vacation_allocation_days = sum(vacation_allocation.mapped('number_of_days'))
            vacations = leave_request_obj.search([('employee_id', '=', rec.employee_id.id),
                                                  ('state', 'in', ('validate', 'validate1')),
                                                  ('leave_type', '=', 'vacation'),
                                                  ('holiday_status_id', '=', rec.leave_type_id.id)])
            vacation_days = sum(vacations.mapped('number_of_days'))
            rec.vacation_balance = vacation_allocation_days - vacation_days

    employee_id = fields.Many2one('hr.employee', string='Employee')
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    vacation_monthly_allowance = fields.Integer('Vacation Monthly Allowance')
    vacation_balance = fields.Integer('Vacation Balance', compute='_cal_vaca_bal_by_type')


class Employee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    @api.model_create_multi
    def create(self, vals_lst):
        leave_alloc_obj = self.env['hr.leave.allocation']
        res = super(Employee, self).create(vals_lst)
        """This will create Vacation and Leave Lines with Leave type,Balance and Allowance on create of Employee."""
        for rec in res:
            rec_name = rec and rec.name or '/'
            res_leave = []
            res_vacation = []
            dep_lines = self.env['leaves.by.department'].search([('department_id', '=', rec.department_id.id)])
            # create leave allocation & LeaveBalanaceByType Line of Employee Based on Department line
            # configured in Leave Type
            for dep_line in dep_lines:
                if dep_line.hr_leave_type_id.leave_type == 'leave':
                    leave_alloc_vals = {
                        'name': 'Monthly Leave Allocation for ' + rec_name,
                        'employee_id': rec.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'regular',
                        'leave_type': 'leave',
                        'number_of_days': dep_line.yearly_balance,
                        'holiday_status_id': dep_line.hr_leave_type_id.id,
                        'department_id': rec.department_id.id
                    }
                    leave_alloc = leave_alloc_obj.create(leave_alloc_vals)
                    leave_alloc.action_approve()
                    if leave_alloc.state == 'validate1':
                        leave_alloc.action_validate()

                    vals_rec = {
                        'employee_id': rec.id,
                        'leave_type_id': dep_line.hr_leave_type_id.id,
                        'leave_monthly_allowance': dep_line.monthly_allowance
                    }
                    res_leave.append((0, 0, vals_rec))

                if dep_line.hr_leave_type_id.leave_type == 'vacation':

                    vacation_alloc_vals = {
                        'name': 'Monthly Vacation Allocation for ' + rec_name,
                        'employee_id': rec.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'regular',
                        'leave_type': 'vacation',
                        'number_of_days': dep_line.yearly_balance,
                        'holiday_status_id': dep_line.hr_leave_type_id.id,
                        'department_id': rec.department_id.id
                    }
                    vacation_alloc = leave_alloc_obj.create(vacation_alloc_vals)
                    vacation_alloc.action_approve()
                    if vacation_alloc.state == 'validate1':
                        vacation_alloc.action_validate()
                    vals_rec = {
                        'employee_id': rec.id,
                        'leave_type_id': dep_line.hr_leave_type_id.id,
                        'vacation_monthly_allowance': dep_line.monthly_allowance
                    }
                    res_vacation.append((0, 0, vals_rec))
            rec.update({'employee_leave_balance_by_type_ids': res_leave,
                        'employee_vacation_balance_by_type_ids': res_vacation})
        return res

    # Leave & Vacation Balance
    leave_balance = fields.Float('Leave Balance', compute='_cal_leave_balance')
    vacation_balance = fields.Integer('Vacation Balance', compute='_cal_leave_balance')
    total_leave = fields.Float(compute='_cal_leave_balance', string='Leaves')
    total_vacation = fields.Integer(compute='_cal_leave_balance', string='Vacations')
    total_alloc_leave = fields.Float('Leave Allocations', compute='_cal_leave_balance')
    total_alloc_vacation = fields.Integer('Vacation Allocations', compute='_cal_leave_balance')
    leave_monthly_allowance = fields.Float('Leave Monthly Allowance', compute='_cal_leave_balance')
    vacation_monthly_allowance = fields.Integer('Vacation Monthly Allowance', compute='_cal_leave_balance')
    employee_leave_balance_by_type_ids = fields.One2many('employee.leave.balance.by.type', 'employee_id',
                                                         'Leave Balance')
    employee_vacation_balance_by_type_ids = fields.One2many('employee.vacation.balance.by.type', 'employee_id',
                                                            'Vacation Balance')

    def _load_records_create(self, values):
        return super(Employee,self.with_context(mail_notify_force_send=False))._load_records_create(values)

    def _cal_leave_balance(self):
        leave_by_type = self.env['employee.leave.balance.by.type']
        vacation_by_type = self.env['employee.vacation.balance.by.type']
        leave_alloc_obj = self.env['hr.leave.allocation']
        leave_request_obj = self.env['hr.leave']
        for employee in self:
            leave_allocation = leave_alloc_obj.search([('employee_id', '=', employee.id),
                                                       ('state', 'in', ('validate', 'validate1')),
                                                       ('leave_type', '=', 'leave')])
            leave_allocation_hours = sum(leave_allocation.mapped('number_of_hours_display'))
            employee.total_alloc_leave = leave_allocation_hours
            leaves = leave_request_obj.search([('employee_id', '=', employee.id),
                                               ('state', 'in', ('validate', 'validate1')),
                                               ('leave_type', '=', 'leave'),
                                               ('holiday_status_id.unpaid', '=', False)])

            leave_hours = 0.0
            for leave in leaves:
                leave_hours += math.ceil(leave.end_time - leave.start_time)

            employee.total_leave = leave_hours
            employee.leave_balance = leave_allocation_hours - leave_hours

            leave_allocwance = leave_by_type.search([('employee_id', '=', employee.id)])
            leave_monthly_allowamce = sum(leave_allocwance.mapped('leave_monthly_allowance'))
            employee.leave_monthly_allowance = leave_monthly_allowamce

            vacation_allocation = leave_alloc_obj.search([('employee_id', '=', employee.id),
                                                          ('state', 'in', ('validate', 'validate1')),
                                                          ('leave_type', '=', 'vacation')])
            vacation_allocation_days = sum(vacation_allocation.mapped('number_of_days'))
            employee.total_alloc_vacation = vacation_allocation_days
            vacations = leave_request_obj.search([('employee_id', '=', employee.id),
                                                  ('state', '=', 'validate'),
                                                  ('leave_type', '=', 'vacation'),
                                                  ('holiday_status_id.unpaid', '=', False)])
            vacation_days = sum(vacations.mapped('number_of_days'))
            employee.total_vacation = vacation_days
            employee.vacation_balance = vacation_allocation_days - vacation_days

            vacation_allocwance = vacation_by_type.search([('employee_id', '=', employee.id)])
            vacation_monthly_allowamce = sum(vacation_allocwance.mapped('vacation_monthly_allowance'))
            employee.vacation_monthly_allowance = vacation_monthly_allowamce


    def update_leave_vacation_balance(self):
        return {
            'name': _("Update Leave/Vacation Balance"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'update.leave.vacation.balance',
            'target': 'new',
        }
