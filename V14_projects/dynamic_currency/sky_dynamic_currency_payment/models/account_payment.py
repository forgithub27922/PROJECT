# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Rate', digits=(7, 9))
    inverse_rate = fields.Float(digits=(12, 4), string="Current Inverse Rate")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
                self.journal_id.display_name))

        # Compute amounts.
        write_off_amount = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            counterpart_amount = -self.amount
            write_off_amount *= -1
        elif self.payment_type == 'outbound':
            # Send money.
            counterpart_amount = self.amount
        else:
            counterpart_amount = 0.0
            write_off_amount = 0.0
        if self.inverse_rate > 0.0:
            balance = self.currency_id.with_context(rate=1 / self.inverse_rate)._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
        else:
            balance = self.currency_id.with_context(rate=1 / 1)._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
        counterpart_amount_currency = counterpart_amount
        write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.date)
        write_off_amount_currency = write_off_amount
        currency_id = self.currency_id.id
        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else:  # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency':-counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': balance < 0.0 and -balance or 0.0,
                'credit': balance > 0.0 and balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.payment_debit_account_id.id if balance < 0.0 else self.journal_id.payment_credit_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency + write_off_amount_currency if currency_id else 0.0,
                'currency_id': currency_id,
                'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if write_off_balance:
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency':-write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list

    @api.onchange('inverse_rate')
    def change_inverse_rate(self):
        for rec in self:
            rec.manual_currency_rate = rec.inverse_rate and (1.0 / (rec.inverse_rate))
            rec.move_id.write({'inverse_rate':rec.inverse_rate})
            rec.move_id.with_context(imbalance='no_check').change_currency_rate()
            for line in rec.move_id.line_ids:
                line.inverse_rate = rec.inverse_rate
                line.change_inverse_rate()

    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        if vals.get('inverse_rate'):
            self.move_id.inverse_rate = vals.get('inverse_rate')
            if vals.get('inverse_rate') > 0:
                self.move_id.manual_currency_rate = 1 / vals.get('inverse_rate')
                self.move_id.with_context(imbalance='no_check').change_currency_rate()
        return res

    @api.onchange('manual_currency_rate_active', 'currency_id')
    def change_manual_rate(self):
        for rec in self:
            date = fields.Date.today()
            if self.date:
                date = self.date
            currency_rates = self.currency_id._get_rates(self.env.user.company_id, date)
            rec.manual_currency_rate = currency_rates.get(rec.currency_id.id)
            rec.inverse_rate = 1 / currency_rates.get(self.currency_id.id)


    def action_post(self):
        jorunal = self.env['account.move'].browse(self.move_id.id)
        if self.manual_currency_rate_active == True:
            jorunal.write({
                "manual_currency_rate_active": True,
                "inverse_rate": self.inverse_rate
            })
            jorunal.line_ids.write({
                "rate": 1 / self.inverse_rate,
                "inverse_rate": self.inverse_rate
            })
        return super(AccountPayment, self).action_post()

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(AccountPayment, self).create(vals_list)
    #     invoice = self.env['account.move'].search([('name', '=', res.ref)])
    #     if invoice:
    #         res.update({
    #             'manual_currency_rate_active': True,
    #             'manual_currency_rate': invoice.manual_currency_rate,
    #             'inverse_rate': invoice.inverse_rate,
    #         })
    #     return res