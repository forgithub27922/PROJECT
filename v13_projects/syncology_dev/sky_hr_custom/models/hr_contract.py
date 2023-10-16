from odoo import models, fields


class ContractType(models.Model):
    _name = 'hr.employee.contract.type'
    _description = 'Contract Types'

    name = fields.Char('Name')
    code = fields.Char('Code')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)