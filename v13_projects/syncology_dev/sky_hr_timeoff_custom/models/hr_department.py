# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Department(models.Model):
    _inherit = 'hr.department'

    @api.model
    def auto_leave_allocation(self):
        """
        This method is used to assign no of leave days and no of vacation days to employees
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        emp_obj = self.env['hr.employee']
        leave_alloc_obj = self.env['hr.leave.allocation']
        if self._context.get('create_allocation'):
            department_ids = self._context.get('create_allocation').department_id

        else:
            department_ids = self.search([])

        for dept in department_ids:
            if self._context.get('create_allocation'):
                employee_ids = self._context.get('create_allocation')
            else:
                employee_ids = emp_obj.search([('department_id', '=', dept.id)])

            for emp in employee_ids:
                if dept.leave_alloc_days:
                    # Leave Allocation
                    leave_alloc_vals = {
                        'name': 'Monthly Leave Allocation for ' + emp.name,
                        'employee_id': emp.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'regular',
                        'leave_type': 'leave',
                        'number_of_days': dept.leave_alloc_days
                    }
                    leave_alloc = leave_alloc_obj.create(leave_alloc_vals)
                    leave_alloc.action_approve()
                if dept.vacation_alloc_days:
                    # Vacation Allocation
                    vacation_alloc_vals = {
                        'name': 'Monthly Vacation Allocation for ' + emp.name,
                        'employee_id': emp.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'regular',
                        'leave_type': 'vacation',
                        'number_of_days': dept.vacation_alloc_days
                    }
                    vacation_alloc = leave_alloc_obj.create(vacation_alloc_vals)
                    vacation_alloc.action_approve()

    @api.onchange('parent_id')
    def onchange_parent_department(self):
        self.working_schedule_id = self.parent_id.working_schedule_id.id

    @api.model
    def create(self, vals):
        # On create of Department this will create Department line in Leave Types
        res = super(Department, self).create(vals)
        leave_types = self.env['hr.leave.type'].search([])
        for leave_type in leave_types:
            leave_type.leaves_by_department_ids = [(0, 0, {'department_id': res.id})]
        return res

    def unlink(self):
        # On delete of Department this will delete Department line in Leave Types
        for rec in self:
            for leave_type in self.env['hr.leave.type'].search([]):
                for leaves_by_department_id in leave_type.leaves_by_department_ids:
                    if leaves_by_department_id.department_id.id == rec.id:
                        leave_type.write({'leaves_by_department_ids': [(2, leaves_by_department_id.id)]})
        return super(Department, self).unlink()
