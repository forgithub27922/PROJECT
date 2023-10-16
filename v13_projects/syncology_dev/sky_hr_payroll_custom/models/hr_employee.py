# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta as rd
from odoo.exceptions import UserError,ValidationError


class Employee(models.Model):
    _inherit = 'hr.employee'

    addition_ids = fields.One2many('hr.addition', 'employee_id', 'Additions')
    penalty_ids = fields.One2many('hr.penalty', 'employee_id', 'Penalties')
    addition_rate = fields.Float('Addition Rate', default='1')
    penalty_rate = fields.Float('Penalty Rate', default='1')
    salary_schedule = fields.Selection([('1', '1st of Month'),
                                        ('15', '15th of Month')
                                        ],
                                       'Salary Schedule', default='1')
    next_salary_date = fields.Date('Next Salary Date')

    def export_data(self, fields_to_export):
        """ Export fields for selected objects

            :param fields_to_export: list of fields
            :param raw_data: True to return value in native Python type
            :rtype: dictionary with a *datas* matrix

            This method is used when exporting data via client menu
            Overridden this method to hide the confidential salary fields.
        """
        mngr_grp_id = self.env.ref('sky_hr_payroll_custom.group_payroll_manager').id
        user_grp_ids = self.env.user.groups_id.ids
        if mngr_grp_id not in user_grp_ids:
            fields_to_check = [
                'is_confidential', 'salary', 'annual_bonus', 'starting_date', 'addition_rate',
                'penalty_rate', 'salary_schedule', 'next_salary_date', 'hourly_rate', 'insurance',
                'ins_cut_value', 'fellowship_fund', 'fellowship_cut_value', 'staff_children_cut',
                'other_cut', 'senior_allowance', 'transition_allowance', 'lms_allowance',
                'travel_allowance_driver', 'supervision_maintenance_allowance', 'other_allowance'
            ]
            for fld in fields_to_check:
                if fld in fields_to_export:
                    fields_to_export.remove(fld)
        fields_to_export = [models.fix_import_export_id_paths(f) for f in fields_to_export]
        return {'datas': self._export_rows(fields_to_export)}

    @api.constrains('addition_rate')
    def _check_addition_rate(self):
        if self.addition_rate < 1:
            raise UserError(_('Addition rate should be greater than or equal to 1!'))

    @api.constrains('penalty_rate')
    def _check_penalty_rate(self):
        if self.penalty_rate < 1:
            raise UserError(_('Penalty rate should be greater than or equal to 1!'))

    @api.onchange('salary_schedule')
    def onchange_schedule(self):
        """
        This method is used to set the next salary date
        -----------------------------------------------
        @param self: object pointer
        """
        cr_date = fields.Date.today()
        for emp in self:
            next_salary_date = False
            if emp.salary_schedule:
                if emp.salary_schedule == '1':
                    next_salary_date = cr_date + rd(day=1)
                elif emp.salary_schedule == '15':
                    next_salary_date = cr_date + rd(day=15)
                if next_salary_date < cr_date:
                    next_salary_date += rd(months=1)
                emp.next_salary_date = next_salary_date

    @api.model
    def cron_create_salary(self):
        """
        This method will create salary for all the employees who have next salary date as current date
        ----------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        salary_obj = self.env['hr.employee.salary']
        penalty_obj = self.env['hr.penalty']
        add_obj = self.env['hr.addition']
        cr_date = fields.Date.today()
        # Search for employees who's salary is due today
        emps = self.search([('next_salary_date', '=', cr_date)])
        # Get Salary Start Date and End Date
        sal_start_date = cr_date - rd(months=1)
        sal_end_date = cr_date - rd(days=1)
        for emp in emps:
            # Create Vals for Salary
            salary_vals = {
                'employee_id': emp.id,
                'start_date': sal_start_date,
                'end_date': sal_end_date,
                'basic': emp.salary,
                'annual_bonus': emp.annual_bonus
            }
            # Add Penalties for the employee
            penalties = penalty_obj.search([('employee_id', '=', emp.id),
                                            ('date', '>=', sal_start_date),
                                            ('date', '<=', sal_end_date),
                                            ('state', '=', 'approved')])
            salary_vals.update({
                'penalty_ids': [(6, 0, penalties.ids)]
            })
            # Add Additions for the employee
            additions = add_obj.search([('employee_id', '=', emp.id),
                                        ('date', '>=', sal_start_date),
                                        ('date', '<=', sal_end_date),
                                        ('state', '=', 'approved')])
            salary_vals.update({
                'addition_ids': [(6, 0, additions.ids)]
            })
            # Create Salary
            salary_obj.create(salary_vals)
            # set the Next Salary Date
            emp.next_salary_date = cr_date + rd(months=1)

    def count_working_hours(self, employee_id, date):
        """
           This method will work hours calculation from the Working Schedules
           ------------------------------------------------------------------
           @param self: object pointer
        """
        working_schedule = employee_id.resource_calendar_id
        if employee_id.schedule_time_ids:
            schedule = self.env['schedule.time'].search([('employee_id', '=', employee_id.id),
                                                         ('from_date', '<=', date.strftime('%d')),
                                                         ('to_date', '>=', date.strftime('%d'))], limit=1)

            if not schedule.id:
                schedule = self.env['schedule.time'].search([('employee_id', '=', employee_id.id),
                                                             ('from_date', '=', 0),
                                                             ('to_date', '=', 0)], limit=1)
            if schedule.id:
                working_schedule = schedule.working_schedule_id

        working_hours = 0.0
        for attendance in working_schedule.attendance_ids:
            weekday = '0' if attendance.dayofweek == '6' else str(int(attendance.dayofweek) + 1)
            if weekday == date.strftime('%w'):
                working_hours += attendance.working_hours
        return working_hours

    def write(self, vals):
        """
        Overridden write method to check the salary fields being updated by payroll manager only.
        It also sets the access for the parent if an employee is added as a manager to any employee.
        --------------------------------------------------------------------------------------------
        :param vals: A dictionary containing fields and values
        :return: True
        """
        # Check the fields being updated only by Payroll Manager
        fields_to_check = [
            'is_confidential', 'salary', 'annual_bonus', 'starting_date', 'addition_rate',
            'penalty_rate', 'salary_schedule', 'next_salary_date', 'hourly_rate', 'insurance',
            'ins_cut_value', 'fellowship_fund', 'fellowship_cut_value', 'staff_children_cut',
            'other_cut', 'senior_allowance', 'transition_allowance', 'lms_allowance',
            'travel_allowance_driver', 'supervision_maintenance_allowance', 'other_allowance'
        ]
        flds_chk = set(fields_to_check)
        flds_vls = set(vals.keys())
        result = flds_chk.intersection(flds_vls)
        if result and not self.env.user.has_group('sky_hr_payroll_custom.group_payroll_manager'):
            raise ValidationError(_("Only Payroll Manager is allowed to Enter Salary Section Fields!"))
        res = super(Employee, self).write(vals)
        # Set the payroll user access for the manager of the employee
        group_id = self.env.ref('sky_hr_payroll_custom.group_payroll_user')
        existing_user_id = self.parent_id and self.parent_id.user_id
        existing_emp = self.parent_id
        if not self._context.get('rec_update'):
            if vals.get('parent_id'):
                # Set the manager group for the employee's manager.
                emp = self.browse(vals.get('parent_id'))
                if emp and emp.child_ids:
                    emp.user_id.write({'groups_id': [(4, group_id.id)]})
            else:
                # Remove the manager group if the employee is not a manager to any employee.
                if not existing_emp.child_ids:
                    existing_user_id.with_context(rec_update=True).write({'groups_id': [(3, group_id.id)]})
        return res

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to check the fields being updated by payroll manager or not.
        -------------------------------------------------------------------------------------
        :param vals_lst: A list of dictionaries containing fields and values
        :return: Recordset of newly created records
        """
        for vals in vals_lst:
            # Raise Warning if Salary is updated by other than Payroll manager
            fields_to_check = [
                'is_confidential', 'salary', 'annual_bonus', 'starting_date', 'addition_rate',
                'penalty_rate', 'salary_schedule', 'next_salary_date', 'hourly_rate', 'insurance',
                'ins_cut_value', 'fellowship_fund', 'fellowship_cut_value', 'staff_children_cut',
                'other_cut', 'senior_allowance', 'transition_allowance', 'lms_allowance',
                'travel_allowance_driver', 'supervision_maintenance_allowance', 'other_allowance'
            ]
            flds_chk = set(fields_to_check)
            flds_vls = set(vals.keys())
            result = flds_chk.intersection(flds_vls)
            if result and not self.env.user.has_group('sky_hr_payroll_custom.group_payroll_manager'):
                raise ValidationError(_("Only Payroll Manager is allowed to Update Salary Section Fields!"))
        return super(Employee, self).create(vals_lst)


