from odoo import models, api, fields


class Zip(models.Model):
    _inherit = "res.city.zip"

    #city = fields.Char('City', required=True)

    state_id = fields.Many2one(
        'res.country.state',
        'State',
    )
    country_id = fields.Many2one('res.country', 'Country')

    


class ResPartner(models.Model):
    _inherit = 'res.partner'

    city = fields.Char(required=True)
