from odoo import models, fields , exceptions, _


class Employee(models.Model):
    _inherit = 'hr.employee'
    
    listed_for_fingerprint = fields.Boolean("Listed for Fingerprint", copy=False)

    def create_sign_in_entry(self):
        self.ensure_one()
        action_date = fields.Datetime.now()
        vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
        return self.env['hr.attendance'].create(vals)
    
    def create_sign_out_entry(self):
        self.ensure_one()
        action_date = fields.Datetime.now()
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance:
            attendance.check_out = action_date
        else:
            raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance
