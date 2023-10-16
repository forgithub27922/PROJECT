from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    no_of_customer = fields.Integer('Number Of Customers')
    customer_mob_no = fields.Char('Customer Mobile Number')
    hotel_open = fields.Boolean('Hotel Open ?')
    amenities_availabel = fields.Selection([('yes', 'YES'), ('no', 'NO')], string='Amenities Availabel')
