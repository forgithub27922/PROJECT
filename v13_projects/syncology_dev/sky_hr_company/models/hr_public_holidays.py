from odoo import models, fields, api


class PublicHolidaysLine(models.Model):
    _inherit = 'hr.public.holidays.line'
    _description = 'Public Holidays'

    company_id = fields.Many2one('res.company', 'School', default=lambda self: self.env.company.id)