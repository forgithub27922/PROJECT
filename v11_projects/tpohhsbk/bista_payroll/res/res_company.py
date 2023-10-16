# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, tools, _


class Company(models.Model):
    _inherit = "res.company"

    consolidate_batch_payslip = fields.Boolean('Consolidate Batch Payslip')
