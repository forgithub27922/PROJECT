from odoo import api, fields, models, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    overtime_rate_weekday = fields.Float(string="Overtime Rate/Hours")
    overtime_rate_weekend = fields.Float(string="Overtime Weekend/Hours")
    ot_calculation_type = fields.Selection([('hourly', 'Hourly'),('monthly', 'Monthly')],
                                           help="If hourly is selected weekend OT rate will be calculated if worked on weekend or holiday")

class Department(models.Model):
    _inherit = "hr.department"

    overtime_rate_weekday = fields.Float(string="Overtime Rate/Hours")
    overtime_rate_weekend = fields.Float(string="Overtime Weekend/Hours")


class Company(models.Model):
    _inherit = "res.company"

    overtime_rate_weekday = fields.Float(string="Overtime Rate/Hours")
    overtime_rate_weekend = fields.Float(string="Overtime Weekend/Hours")


# class DesignationGrade(models.Model):
#     _inherit = 'designation.grade'
# 
#     overtime_rate_weekday = fields.Float(string="Overtime Rate/Hours")
#     overtime_rate_weekend = fields.Float(string="Overtime Weekend/Hours")
