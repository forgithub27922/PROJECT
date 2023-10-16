# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one(default=lambda self: self._get_analytic_account())

    @api.model
    def _get_analytic_account(self):
        if self.env.user:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            if employee and employee.sudo().department_id and employee.sudo().department_id.company_id.id == self.env.user.company_id.id:
                analytic_account_id = employee.department_id.analytic_id
                return analytic_account_id
