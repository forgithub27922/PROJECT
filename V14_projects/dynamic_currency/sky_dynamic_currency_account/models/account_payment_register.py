from odoo import fields, models, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    manual_currency_rate = fields.Float('Rate', digits=(7, 9))
    inverse_rate = fields.Float(digits=(12, 4), string="Current Inverse Rate")

    @api.depends('inverse_rate', 'source_amount', 'source_amount_currency', 'source_currency_id', 'company_id',
                 'currency_id', 'payment_date')
    def _compute_amount(self):
        for wizard in self:
            # if wizard.source_currency_id == wizard.currency_id:
            if wizard.company_id.currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
                if self.inverse_rate:
                    wizard.amount = wizard.company_id.currency_id.with_context(rate=1 / wizard.inverse_rate)._convert(
                        wizard.amount, wizard.currency_id, wizard.company_id, wizard.payment_date)

            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount,
                                                                                 wizard.currency_id, wizard.company_id,
                                                                                 wizard.payment_date)
                wizard.amount = amount_payment_currency
                if wizard.inverse_rate:
                    wizard.amount = wizard.company_id.currency_id.with_context(rate=1 / wizard.inverse_rate)._convert(
                        wizard.amount, wizard.currency_id, wizard.company_id, wizard.payment_date)


    @api.model
    def default_get(self, fields_list):
        res = super(AccountPaymentRegister, self).default_get(fields_list)
        invoice = self.env['account.move'].search([('id', '=', self._context.get('active_ids'))])
        if len(invoice) == 1:
            if invoice.inverse_rate > 0.0:
                res.update({
                    'manual_currency_rate': invoice.manual_currency_rate,
                    'inverse_rate': invoice.inverse_rate,
                })
        return res

    def _create_payment_vals_from_wizard(self):
        print("s\n\n\elffff", self.inverse_rate)
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'manual_currency_rate_active': True,
            'manual_currency_rate': 1 / self.inverse_rate,
            'inverse_rate': self.inverse_rate,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals


    @api.onchange('inverse_rate')
    def change_inverse_rate(self):
        if self.inverse_rate > 0.0:
            self.manual_currency_rate = 1 / self.inverse_rate
