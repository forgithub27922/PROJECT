from odoo import models, fields


class EmployeeStatus(models.Model):
    _name = 'hr.employee.status'
    _description = 'Employee Status'

    name = fields.Char('Name')
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
