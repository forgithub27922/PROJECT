from odoo import models, fields


class EmployeeGrade(models.Model):
    _name = 'employee.grade'
    _description = 'Employee Grade'

    name = fields.Char('Grade')
