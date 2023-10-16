from odoo import models, fields


class Employee(models.Model):
    _inherit = 'hr.employee'

    employee_grade_ids = fields.Many2many(comodel_name='employee.grade', string ='Grade')
