# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    type = fields.Selection([('voluntary', 'Voluntarily'),
                             ('forced', 'Forced')],
                            string='Type of Separation')


class AssetEmployee(models.Model):
    _inherit = 'employee.assets'

    termination_id = fields.Many2one('hr.termination.request')
