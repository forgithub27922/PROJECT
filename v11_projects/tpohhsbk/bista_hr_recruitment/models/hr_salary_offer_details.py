# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class HrSalaryOfferDetails(models.Model):
    _name = 'hr.salary.offer.details'
    _description = "Salary Offer Details"

    name = fields.Char('Applicant Name')
    date = fields.Date()
    struct_id = fields.Many2one('hr.payroll.structure', 'Salary Structure')
    salary_detail_lines = fields.One2many(
        'hr.salary.offer.details.line', 'salary_detail_id',
        string='Salary Lines')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class HrSalaryOfferDetailsLine(models.Model):
    _name = 'hr.salary.offer.details.line'
    _description = "Salary Offer Details Line"
    _order = "sequence"

    name = fields.Char()
    code = fields.Char()
    sequence = fields.Integer('Sequence')
    category_id = fields.Many2one('hr.salary.rule.category', 'Category')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Rule')
    total = fields.Float('Total')
    salary_detail_id = fields.Many2one('hr.salary.offer.details',
                                       string='Offer Detail ID')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)