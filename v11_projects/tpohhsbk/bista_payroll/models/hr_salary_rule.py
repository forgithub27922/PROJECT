from odoo import api, fields, models, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    parent_id = fields.Many2one('hr.payroll.structure', string='Parent',
                                default=False)