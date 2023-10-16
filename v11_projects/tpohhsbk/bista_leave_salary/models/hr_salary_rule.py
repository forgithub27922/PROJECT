# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, _

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_hra = fields.Boolean('Included in Leave Salary', defaul='false')