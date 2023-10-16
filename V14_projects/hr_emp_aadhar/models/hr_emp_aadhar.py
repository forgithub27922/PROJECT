from odoo import models,fields

class HrEmployeePrivate(models.Model):
    _inherit = 'HR.employee'

    aadhar_no = fields.Char('Aadhar Number', size=14)