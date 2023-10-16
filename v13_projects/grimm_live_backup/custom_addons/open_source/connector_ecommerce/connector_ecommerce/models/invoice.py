# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.move' #odoo13change

    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for record in self:
            self._event('on_invoice_paid').notify(record)
        return res

    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        for record in self:
            self._event('on_invoice_validated').notify(record)
        return res
