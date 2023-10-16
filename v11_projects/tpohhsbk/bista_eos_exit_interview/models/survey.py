# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SurveyUserInput(models.Model):

    _inherit = 'survey.user_input'

    user_id = fields.Many2one('res.users', string='User')
    employee_id = fields.Many2one('hr.employee', string='Employee')

    @api.model
    def create(self, vals):
        """
        Set employee once survey is filled or create by employee.
        :param vals:
        :return: super with updated vals
        """
        employee_env = self.env['hr.employee']
        emp_exists = employee_env.search([('user_id', '=', self._uid)])
        if emp_exists:
            vals.update({'employee_id': emp_exists[0].id})
        vals.update({'user_id': self._uid})
        return super(SurveyUserInput, self).create(vals)
