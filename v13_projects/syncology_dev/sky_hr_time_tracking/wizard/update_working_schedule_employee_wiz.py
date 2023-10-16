from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError


class UpdateEmployeeWorkingScheduleWizard(models.TransientModel):
    _name = 'update.working.employee.schedule.wiz'
    _description = 'Update Working Schedule of Employee Wizard'

    employee_ids = fields.Many2many('hr.employee', 'update_for_working_schedule_wiz_hr_employee_rel',
                                    'working_schedule_id', 'employee_id', 'Employee')
    schedule_time_ids = fields.One2many('employee.record.update', 'update_emp_schedule_id', 'Schedule')

    @api.onchange('schedule_time_ids')
    def onchange_employee_schedule_time(self):
        number_lst = [num for num in range(0, 32)]
        line_number_lst = []
        for emp in self:
            blank_lines = emp.schedule_time_ids.filtered(lambda x: x.from_date == 0 and x.to_date == 0)
            for line in emp.schedule_time_ids:
                if line.from_date not in number_lst:
                    raise ValidationError("Start Date Must be between 1 to 31")
                elif line.to_date not in number_lst:
                    raise ValidationError("End Date Must be between 1 to 31")
                elif line.from_date and line.to_date and line.from_date >= line.to_date:
                    raise ValidationError("End Date Must be Greater Than Start Date")
                elif line.to_date and not line.from_date:
                    raise ValidationError("Start Date Must be required")
                elif line.from_date and not line.to_date:
                    raise ValidationError("End Date Must be required")
                elif len(blank_lines) > 1:
                    raise ValidationError("You should not keep more than one blank record")
                if line.from_date not in line_number_lst and line.to_date not in line_number_lst:
                    line_number_lst += [num for num in range(line.from_date, line.to_date + 1)]
                else:
                    raise ValidationError("You can't Overlap Date")

    def action_confirm(self):
        self.employee_ids.write({'schedule_time_ids': [(5, 0, 0)]})
        schedule_lst = []
        for schedule_time in self.schedule_time_ids:
            schedule_lst.append((0, 0, {'from_date': schedule_time.from_date, 'to_date': schedule_time.to_date,
                                        'working_schedule_id': schedule_time.working_schedule_id.id}))
        self.employee_ids.write({'schedule_time_ids': schedule_lst})


class UpdateEmployee(models.TransientModel):
    _name = 'employee.record.update'
    _description = 'Updating The Record Of Employee'

    from_date = fields.Integer("From", limit=2)
    to_date = fields.Integer("To", limit=2)
    working_schedule_id = fields.Many2one('resource.calendar', string="Working Schedule")
    update_emp_schedule_id = fields.Many2one('update.working.employee.schedule.wiz', string="Working Employee Schedule")

