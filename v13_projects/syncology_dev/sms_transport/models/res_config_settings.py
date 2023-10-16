from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    extra_activity_id = fields.Many2one('extra.activity', related='company_id.extra_activity_id',
                                        string='Extra Activity', readonly=False)
    job_position_id = fields.Many2one('hr.job', related='company_id.job_position_id', string='Job Position',
                                      readonly=False)
    transport_fee_type_id = fields.Many2one('fee.type', related='company_id.transport_fee_type_id', string='Transport Fee Type',
                                     readonly=False)
