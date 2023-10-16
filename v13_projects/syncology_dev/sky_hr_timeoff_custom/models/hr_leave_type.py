from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    _description = 'Hr Leave Type'

    def _get_all_departments(self):
        # This method will get all departments in Leave type's Department
        departments = self.env['hr.department'].search([])
        res = []
        for rec in departments:
            vals = {
                'department_id': rec.id,
                'hr_leave_type_id': self.id
            }
            res.append((0, 0, vals))
        return res

    leave_type = fields.Selection([('vacation', 'Vacation'),
                                   ('leave', 'Leave')], 'Leave Type')
    unpaid = fields.Boolean("Unpaid")
    request_unit = fields.Selection([
        ('day', 'Day'), ('half_day', 'Half Day'), ('hour', 'Hours')],
        default='hour', string='Take Time Off in', required=True)
    leaves_by_department_ids = fields.One2many('leaves.by.department', 'hr_leave_type_id', 'Departments',
                                               default=_get_all_departments)
    responsible_ids = fields.Many2many('res.users', string='Responsible')

    @api.onchange('validation_type')
    def onchange_validation_type(self):
        for validation in self:
            validation.responsible_ids = [(6, 0, [])]

    @api.model
    def auto_leave_allocation(self):
        """
        This method is used to assign no of leave days and no of vacation days to employees as per Leave types
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        res = {}
        leaves_by_dep_ids = self.env['leaves.by.department'].search([])
        emp_obj = self.env['hr.employee']
        leave_alloc_obj = self.env['hr.leave.allocation']

        for leaves_by_dep_id in leaves_by_dep_ids:
            if res and res.get(leaves_by_dep_id.department_id, False):
                res[leaves_by_dep_id.department_id].append(tuple((leaves_by_dep_id.hr_leave_type_id.id,
                                                                  leaves_by_dep_id.monthly_allowance,
                                                                  leaves_by_dep_id.yearly_balance,
                                                                  leaves_by_dep_id.hr_leave_type_id.leave_type)))
            else:
                res[leaves_by_dep_id.department_id] = [tuple((leaves_by_dep_id.hr_leave_type_id.id,
                                                              leaves_by_dep_id.monthly_allowance,
                                                              leaves_by_dep_id.yearly_balance,
                                                              leaves_by_dep_id.hr_leave_type_id.leave_type))]

        for rec_key, rec_value in res.items():
            for emp in emp_obj.search([('department_id', '=', rec_key.id)]):
                for rec in rec_value:
                    if rec[2] > 0:
                        if rec[3] == 'leave':
                            emp_leave_bal_lines = self.env['employee.leave.balance.by.type'].search([
                                ('employee_id', '=', emp.id),
                                ('leave_type_id', '=', rec[0])])
                            leaves_days = sum(emp_leave_bal_lines.mapped('leave_balance'))
                            leaves_days = rec[2] - leaves_days
                            if leaves_days != 0:
                                # Leave Allocation
                                leave_alloc_vals = {
                                    'name': 'Monthly Leave Allocation for ' + emp.name,
                                    'employee_id': emp.id,
                                    'holiday_type': 'employee',
                                    'allocation_type': 'regular',
                                    'leave_type': 'leave',
                                    'number_of_days': leaves_days,
                                    'holiday_status_id': rec[0],
                                    'department_id': rec_key.id
                                }
                                leave_alloc = leave_alloc_obj.create(leave_alloc_vals)
                                leave_alloc.action_approve()
                                if leave_alloc.state == 'validate1':
                                    leave_alloc.action_validate()
                        if rec[3] == 'vacation':
                            emp_vacation_bal_lines = self.env['employee.vacation.balance.by.type'].search([
                                ('employee_id', '=', emp.id),
                                ('leave_type_id', '=', rec[0])])
                            vacation_days = sum(emp_vacation_bal_lines.mapped('vacation_balance'))
                            vacation_days = rec[2] - vacation_days
                            if vacation_days != 0:
                                # Vacation Allocation
                                vacation_alloc_vals = {
                                    'name': 'Monthly Vacation Allocation for ' + emp.name,
                                    'employee_id': emp.id,
                                    'holiday_type': 'employee',
                                    'allocation_type': 'regular',
                                    'leave_type': 'vacation',
                                    'number_of_days': vacation_days,
                                    'holiday_status_id': rec[0],
                                    'department_id': rec_key.id
                                }
                                vacation_alloc = leave_alloc_obj.create(vacation_alloc_vals)
                                vacation_alloc.action_approve()
                                if vacation_alloc.state == 'validate1':
                                    vacation_alloc.action_validate()


class LeavesByDepartment(models.Model):

    _name = 'leaves.by.department'
    _description = "Leaves By Department"

    department_id = fields.Many2one('hr.department', string='Department')
    yearly_balance = fields.Integer('Yearly Balance', default=0)
    monthly_allowance = fields.Integer('Monthly Allowance', default=0)
    hr_leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')

    def create_leave_lines(self):
        for rec in self:
            if rec.department_id:
                employee_ids = self.env['hr.employee'].search([('department_id', '=', rec.department_id.id)])
                for emp in employee_ids:
                    if rec.hr_leave_type_id.leave_type == 'leave':
                        leave_bal_line = self.env['employee.leave.balance.by.type'].search([
                            ('employee_id', '=', emp.id),
                            ('leave_type_id', '=', rec.hr_leave_type_id.id)
                        ])
                        if leave_bal_line:
                            leave_bal_line.leave_monthly_allowance = rec.monthly_allowance
                        else:
                            vals_rec = {
                                'employee_id': emp.id,
                                'leave_type_id': rec.hr_leave_type_id.id,
                                'leave_monthly_allowance': rec.monthly_allowance
                            }
                            emp.employee_leave_balance_by_type_ids = [(0, 0, vals_rec)]
                    if rec.hr_leave_type_id.leave_type == 'vacation':
                        vacation_bal_line = self.env['employee.vacation.balance.by.type'].search([
                            ('employee_id', '=', emp.id),
                            ('leave_type_id', '=', rec.hr_leave_type_id.id)
                        ])
                        if vacation_bal_line.ids:
                            vacation_bal_line.vacation_monthly_allowance = rec.monthly_allowance
                        else:
                            vals_rec = {
                                'employee_id': emp.id,
                                'leave_type_id': rec.hr_leave_type_id.id,
                                'vacation_monthly_allowance': rec.monthly_allowance
                            }
                            emp.employee_vacation_balance_by_type_ids = [(0, 0, vals_rec)]

    def write(self, vals):
        """On update Department lines in Leave types, this will create/update Leave/Vacation Balance
        Table of Employee"""
        res = super(LeavesByDepartment, self).write(vals)
        self.create_leave_lines()
        return res

    def create(self, vals):
        """On create of Department lines in Leave types, this will create/update Leave/Vacation Balance
        Table of Employee"""
        res = super(LeavesByDepartment, self).create(vals)
        res.create_leave_lines()
        return res

