from odoo import models, fields


class CustomerCity(models.Model):
    _name = 'customer.city'
    _desc = 'City'
    _rec_name = 'city'
    city = fields.Char('City')
    city_code = fields.Char('City Code')
