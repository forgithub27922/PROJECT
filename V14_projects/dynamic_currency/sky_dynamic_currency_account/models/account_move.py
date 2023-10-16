# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    inverse_rate = fields.Float(
        'Inverse Rate', digits=(12, 4),
        help='The rate of the currency from the currency of rate 1 (0 if no '
             'rate defined).'
    )
    rate = fields.Float(digits=(7, 9))

    @api.onchange('inverse_rate','product_id', 'price_unit')
    def change_inverse_rate(self):
        for rec in self:
            rec.rate = rec.inverse_rate and (1.0 / (rec.inverse_rate))
            if rec.inverse_rate > 0:
                rec.with_context(rate=1 / rec.inverse_rate)._onchange_amount_currency()

    @api.onchange('amount_currency', 'currency_id', 'debit', 'credit', 'tax_ids', 'account_id', 'price_unit',
                  'quantity', 'product_id')
    def _onchange_mark_recompute_taxes(self):
        print("call this method in account move line")
        ''' Recompute the dynamic onchange based on taxes.
        If the edited line is a tax line, don't recompute anything as the user must be able to
        set a custom value.
        '''
        for line in self:
            if not line.tax_repartition_line_id:
                line.recompute_tax_line = True
            if line.move_id.manual_currency_rate_active == True:
                line.inverse_rate = line.move_id.inverse_rate
                line.rate = line.move_id.manual_currency_rate
            self.move_id.change_currency_rate()


class AccountMove(models.Model):
    _inherit = 'account.move'

    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Rate', digits=(7, 9))
    inverse_rate = fields.Float(digits=(12, 4), string="Current Inverse Rate")

    @api.onchange('inverse_rate')
    def change_inverse_rate(self):
        for rec in self:
            if rec.inverse_rate > 0:
                rec.manual_currency_rate = rec.inverse_rate and (1.0 / (rec.inverse_rate))

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(self.env['account.move.line']._fields)
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            # for account payment
            if not self._context.get('imbalance'):
                raise UserError(
                    _("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))

    @api.onchange('manual_currency_rate_active', 'currency_id', 'invoice_date')
    def change_manual_rate(self):
        for rec in self:
            date = fields.Date.today()
            if self.invoice_date:
                date = self.invoice_date
            currency_rates = self.currency_id._get_rates(self.env.user.company_id, date)
            rec.manual_currency_rate = currency_rates.get(rec.currency_id.id)
            rec.inverse_rate = 1 / currency_rates.get(self.currency_id.id)
            for line in self.line_ids:
                line.inverse_rate = 1 / currency_rates.get(self.currency_id.id)
                line.change_inverse_rate()
                line._onchange_currency()
                line._onchange_amount_currency()

    # @api.onchange('inverse_rate')
    def change_currency_rate(self):
        for line in self.with_context(imbalance='no_check').line_ids:
            line._onchange_currency()
            line.inverse_rate = self.inverse_rate
            line.change_inverse_rate()
            if self.inverse_rate > 0 and self.manual_currency_rate_active:
                line.with_context(rate=1 / self.inverse_rate)._onchange_amount_currency()
