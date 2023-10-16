# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    department_id = fields.Many2one('hr.department', 'Department')


class HRDepartment(models.Model):
    _inherit = "hr.department"

    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')


class AnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    department_id = fields.Many2one('hr.department', string='Department', help="User's related department",
                                    default=lambda self: self._get_department())
    account_department_id = fields.Many2one(comodel_name='hr.department', related='account_id.department_id',
                                            string='Account Department', store=True, readonly=True,
                                            help="Account's related department")

    @api.model
    def _get_department(self):
        user = self.env.user.id or self._uid
        employee = self.env['hr.employee'].search([('user_id', '=', user)], limit=1)
        if employee and employee.sudo().department_id and employee.sudo().department_id.company_id.id == self.env.user.company_id.id:
            department_id = employee.department_id
            return department_id
