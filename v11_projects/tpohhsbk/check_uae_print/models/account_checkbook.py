# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Account_Checkbook(models.Model):
    _name = 'account.checkbook'

    def get_bank_account(self):
        for rec in self:
            if rec.account_journal_id:
                rec.bank_account_id = rec.account_journal_id.bank_account_id.id
            else:
                rec.bank_account_id = False

    name = fields.Char("Cheque Book Name", required=True, copy=False)
    start_page = fields.Integer("Start Page")
    pages = fields.Integer("End Page")
    account_journal_id = fields.Many2one("account.journal", string="Journal",)
    bank_account_id = fields.Many2one("res.partner.bank", string="Bank Account",compute="get_bank_account")
    printed_page = fields.Integer("Total Printed Pages", default=0,)
    cheque_format_id = fields.Many2one("cheque.format", string="Cheque Format")

    _sql_constraints = [('name', 'unique (name)', "Cheque Book already exists !")]


    def reset_cheque_book(self):
        """ reset cheque book printed pages """
        for rec in self:
            rec.printed_page = 0


class Account_Journal(models.Model):
    _inherit = 'account.journal'

    account_checkbook_id = fields.Many2one("account.checkbook", string="Cheque Book",)
    custom_check_journal = fields.Boolean()











