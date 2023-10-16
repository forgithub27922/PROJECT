from odoo import models, fields, api, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    report_header_id = fields.Many2one('hr.payslip.report.header')
    

class HrPayslipHeader(models.Model):
    _name = 'hr.payslip.report.header'
    
    name = fields.Char("name",required=True)
    company_id = fields.Many2one('res.company',"Company",required=True,
                                 default=lambda self: self.env.user.company_id)
