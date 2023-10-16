# -*- coding: utf-8 -*-

from odoo import models, fields


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    qualification_id = fields.Many2one('grimm.asset.qualification', default=False)

class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    qualification_id = fields.Many2one('grimm.asset.qualification', default=False)
