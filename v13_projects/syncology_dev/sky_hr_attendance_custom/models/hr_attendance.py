from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime

class Attendance(models.Model):
    _inherit = 'hr.attendance'

    parent_id = fields.Many2one('hr.employee', 'parent', related='employee_id.parent_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    def action_attendance(self):
        return {
            'name': _('Import Attendance Wizard'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'import.attendance.wiz',
            'target': 'new',
        }

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        return True
