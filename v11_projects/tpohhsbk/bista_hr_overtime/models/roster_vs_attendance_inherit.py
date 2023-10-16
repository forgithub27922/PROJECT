from odoo import api, fields, models, _


class RosterVsAttendanceLine(models.Model):
    _inherit= 'roster.vs.attendance.line'
    
    overtime_request_id = fields.Many2one(
        'request.overtime',
        string="Overtime Request",
        ondelete="restrict")
    actual_overtime = fields.Float('Actual Overtime')
    overtime = fields.Float('Calculated Overtime')
