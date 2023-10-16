from odoo import models, fields, api


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    tracking_line_id = fields.Many2one('time.tracking.line', 'Tracking Line')

    @api.model_create_multi
    def create(self, vals_lst):
        time_tracking_obj = self.env["time.tracking"]
        att = super(Attendance, self).create(vals_lst)
        time_tracking_line = self.env["time.tracking.line"].search([
            ("employee_id", '=', att.employee_id.id),
            ('date', '=', att.check_in)], limit=1)
        if time_tracking_line:
            time_tracking_line.tracking_id.with_context({'ignore_update': True}).compute_tracking()
        else:
            time_tracking = time_tracking_obj.search([
                ("employee_id", '=', att.employee_id.id),
                ('month', '=', str(att.check_in.month)),
                ('year', '=', att.check_in.year)], limit=1)
            if not time_tracking:
                time_tracking = time_tracking_obj.create({
                    "name": "TIME TRACKING of" + att.employee_id.name + str(att.check_in.month) + \
                            '-' + str(att.check_in.year),
                    "employee_id": att.employee_id.id,
                    'month': str(att.check_in.month),
                    'year': att.check_in.year,
                    "start_date": att.check_in,
                    "end_date": att.check_out,
                    "schedule_id": att.employee_id.resource_calendar_id.id})
            if time_tracking.state == 'open':
                time_tracking.with_context({'ignore_update': True}).generate_tracking()
            time_tracking.with_context({'ignore_update': True}).compute_tracking()
        return att

    def write(self, vals_lst):
        res = super(Attendance, self).write(vals_lst)
        time_tracking_obj = self.env["time.tracking"]
        time_tracking_line_obj = self.env["time.tracking.line"]
        for att in self:
            time_tracking_line = time_tracking_line_obj.search([
                ("employee_id", '=', att.employee_id.id),
                ('date', '=', att.check_in)], limit=1)
            if not self._context.get('ignore_update', False):
                if time_tracking_line:
                    time_tracking_line.tracking_id.with_context({'ignore_update': True}).compute_tracking()
                else:
                    time_tracking = time_tracking_obj.search([
                        ("employee_id", '=', att.employee_id.id),
                        ('month', '=', str(att.check_in.month)),
                        ('year', '=', att.check_in.year)], limit=1)
                    if not time_tracking:
                        time_tracking = time_tracking_obj.create({
                            "name": "Time Tracking of " + att.employee_id.name + " - " \
                                    + str(att.check_in.month) + '-' + str(att.check_in.year),
                            "employee_id": att.employee_id.id,
                            'month': str(att.check_in.month),
                            'year': att.check_in.year,
                            "start_date": att.check_in,
                            "end_date": att.check_out,
                            "schedule_id": att.employee_id.resource_calendar_id.id})
                    if time_tracking.state == 'open':
                        time_tracking.with_context({'ignore_update': True}).generate_tracking()
                    time_tracking.with_context({'ignore_update': True}).compute_tracking()
        return res