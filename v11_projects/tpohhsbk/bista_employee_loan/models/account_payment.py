from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_counterpart_move_line_vals(self, invoice=False):
        context = dict(self._context)
        result = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        if context.get('active_model') == 'hr.employee.loan':
            result.update({'account_id': context.get('loan_account_id')[0]})
        return result