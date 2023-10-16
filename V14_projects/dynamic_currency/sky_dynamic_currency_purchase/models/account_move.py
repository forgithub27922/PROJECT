from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        self._post(soft=False)
        if self.manual_currency_rate_active == True:
            self.change_currency_rate()
        return False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        invoice_obj = self.env['account.move'].browse(res.id)
        invoice_obj.change_inverse_rate()
        invoice_obj.change_currency_rate()
        return res