# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _

class AccountMoveReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        result = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        result["ref"] = "" # move.ref if move.ref else move.name # as per the suggestion from Doris removed ref for credit note
        result["invoice_origin"] = move.invoice_origin if move.invoice_origin else move.name
        return result