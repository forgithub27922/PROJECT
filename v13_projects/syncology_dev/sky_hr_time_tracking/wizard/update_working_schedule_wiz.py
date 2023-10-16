from odoo import models, fields, api, _


class UpdateWorkingScheduleWizard(models.TransientModel):
    _name = 'update.working.schedule.wiz'
    _description = 'Update Working Schedule Wizard'

    department_ids = fields.Many2many('hr.department', 'update_working_schedule_wiz_hr_department_rel',
                                      'working_schedule_id', 'employee_id', 'Department')
    schedule_id = fields.Many2one('resource.calendar', 'Working Schedule')

    def action_confirm(self):
        department_obj = self.env['hr.department']

        for rec in self:
            if rec.department_ids:
                departments = department_obj.browse(rec.department_ids.ids)
                departments.write({'working_schedule_id': rec.schedule_id.id})
            employee_ids = self.env['hr.employee'].search([('department_id','in',rec.department_ids.ids)])
            for employee_id in employee_ids:
                schedule_time_line = self.env['schedule.time'].search([('employee_id', '=', employee_id.id), ('from_date', '=', 0), ('to_date','=',0)], limit=1)
                if schedule_time_line:
                    schedule_time_line.working_schedule_id = rec.schedule_id.id
                else:
                    self.env['schedule.time'].create({'employee_id': employee_id.id,
                                         'from_date':0,
                                         'to_date':0,
                                         'working_schedule_id':rec.schedule_id.id
                                         })








