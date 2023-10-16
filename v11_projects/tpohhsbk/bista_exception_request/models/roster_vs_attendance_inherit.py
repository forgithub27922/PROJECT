from odoo import api, fields, models, _



class RosterVsAttendanceLine(models.Model):
    _inherit= 'roster.vs.attendance.line'
    
    exception_request_id = fields.Many2one('request.exception',
                                           string="Exception Request",
                                           ondelete="restrict")
    exception_hours = fields.Float(string='Exception Hours')