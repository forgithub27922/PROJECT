# -*- encoding: utf-8 -*-
from odoo import fields, models,api,_


class res_bank(models.Model):
    _inherit='res.bank'

    branch_id = fields.Many2one('res.bank.branch',string="Bank Branch")


class res_bank_branch(models.Model):
    _name = 'res.bank.branch'

    name = fields.Char(string="Name")
    bank_id = fields.Many2one('res.bank',string="Bank")