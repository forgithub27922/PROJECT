from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    lm_csv_path = fields.Char('LaserMarker Path')