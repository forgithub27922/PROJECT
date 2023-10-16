from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    overtime_addtion_type_id = fields.Many2one('hr.addition.type','OverTime Addition Type')
    leave_penalty_type_id = fields.Many2one('hr.penalty.type', 'Leave Penalty Type')
    vacation_penalty_type_id = fields.Many2one('hr.penalty.type', 'Vacation Penalty Type')
    late_entry_penalty_type_id = fields.Many2one('hr.penalty.type', 'Late Entry Penalty Type')
    early_exit_penalty_type_id = fields.Many2one('hr.penalty.type', 'Early Exit Penalty Type')
    absence_penalty_type_id = fields.Many2one('hr.penalty.type', 'Absence Penalty Type')