# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    _order = 'sequence'

    analytic_group_id = fields.Many2one('analytic.group', 'Analytic Group')
    sequence = fields.Integer(string="Sequence")

    _sql_constraints = [
        ('analytic_code_uniq', 'unique(code, company_id)',
         'code must be unique per company!'),
        ('analytic_name_uniq', 'unique(name, company_id)',
         'Name must be unique per company!'),
    ]


class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'

    company_id = fields.Many2one('res.company', 'Company')


class  AnalyticGroup(models.Model):
    _name = 'analytic.group'
    _description = 'Analytic Group'

    name = fields.Char('Name')
    account_group_ids = fields.Many2many('account.group', string="Account Group")
