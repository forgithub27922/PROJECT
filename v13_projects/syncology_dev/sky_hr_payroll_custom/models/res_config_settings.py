from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_addtion_type_id = fields.Many2one('hr.addition.type',
                                               related="company_id.overtime_addtion_type_id",
                                               string='OverTime Addition Type',
                                               readonly=False)
    leave_penalty_type_id = fields.Many2one('hr.penalty.type',
                                            related="company_id.leave_penalty_type_id",
                                            string='Leave Penalty Type',
                                            readonly=False)
    vacation_penalty_type_id = fields.Many2one('hr.penalty.type',
                                               related="company_id.vacation_penalty_type_id",
                                               string='Vacation Penalty Type',
                                               readonly=False)
    late_entry_penalty_type_id = fields.Many2one('hr.penalty.type',
                                                 related="company_id.late_entry_penalty_type_id",
                                                 string='Late Entry Penalty Type',
                                                 readonly=False)
    early_exit_penalty_type_id = fields.Many2one('hr.penalty.type',
                                                 related="company_id.early_exit_penalty_type_id",
                                                 string='Early Exit Penalty Type',
                                                 readonly=False)
    absence_penalty_type_id = fields.Many2one('hr.penalty.type',
                                              related="company_id.absence_penalty_type_id",
                                              string='Absence Penalty Type',
                                              readonly=False)