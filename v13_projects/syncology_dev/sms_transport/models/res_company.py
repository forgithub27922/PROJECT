from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    extra_activity_id = fields.Many2one('extra.activity', string='Extra Activity')
    job_position_id = fields.Many2one('hr.job', string='Extra Activity')
    transport_fee_type_id = fields.Many2one('fee.type', string='Transport Fee Type')











