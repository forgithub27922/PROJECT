from odoo import models,fields


class City(models.Model):
    _inherit = 'res.city'

    country_id = fields.Many2one('res.country', string='Country', required=False)

