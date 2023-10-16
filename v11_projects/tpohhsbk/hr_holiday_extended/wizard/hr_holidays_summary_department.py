# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HolidaysSummaryDept(models.TransientModel):
    _inherit = 'hr.holidays.summary.dept'

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def print_report(self):
        if not self.depts:
            self.depts = self.env['hr.department'].search([('company_id', '=', self.company_id.id)]).ids
        return super(HolidaysSummaryDept, self).print_report()
