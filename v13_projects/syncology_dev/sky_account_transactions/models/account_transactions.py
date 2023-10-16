from odoo import models, fields, api, _
from odoo.exceptions import UserError



class AccountTransaction(models.Model):
    _name = 'account.transaction'

    name = fields.Char('Transaction No')
    date = fields.Date('Date', default=fields.date.today(),required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    txn_type = fields.Selection(selection=[('send', 'Send Money'), ('receive', 'Receive Money')],
                                string='Transaction Type',required=True)
    txn_line_ids = fields.One2many('account.transaction.line', 'txn_id', string='Transaction Lines', copy=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('posted', 'Posted'), ('canceled', 'Canceled')],
                             string='State', default='draft')
    move_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency')
    total_amount = fields.Monetary(currency_field='currency_id', compute='_cal_total_amount_lines', string='Total Amount')
    notes = fields.Text(string='Notes')
    ref = fields.Char('Reference')

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create() method to set the sequence on the Transaction
        ------------------------------------------------------------------
        :param vals_lst: A list of dictionary containing fields and values
        :return: A newly created recordset.
        """
        seq_transaction = self.env.ref('sky_account_transactions.transaction_sequence')
        for vals in vals_lst:
            vals.update({
                'name': seq_transaction.next_by_id()
            })
        return super().create(vals_lst)

    @api.onchange('journal_id')
    def onchange_on_currency(self):
        """
        This onchange method uses to change the currency to have the currency of the journal on transaction Model.
        ------------------------------------------------------------------------------------------------------
        @:param self : object pointer.
        """
        for currency in self:
            currency.currency_id = currency.journal_id.currency_id.id or currency.journal_id.company_id.currency_id.id

    @api.depends('txn_line_ids')
    def _cal_total_amount_lines(self):
        """
        This computing method calculates the amount of the transaction line's amount.
        Give the total amount.
        ---------------------------------------------------------------------------
        @:param self:object pointer
        """
        for amount in self:
            total = 0.0
            for am_ln in amount.txn_line_ids:
                total += am_ln.amount
            amount.total_amount = total

    def draft(self):
        """
        This method is used for changing the state to 'DRAFT'.
        And when it is again set to draft move_id will be blank.
        ------------------------------------------------------
        @:param self: object pointer
        """
        for transaction in self:
            transaction.state = 'draft'
            transaction.write({
                'move_id': False
            })

    def post(self):
        """
        This method is used for changing the state to 'POST'.
        And it will create a new record in the journal[account. move] as per the transaction type.
        -----------------------------------------------------------------------------------------
        @param self: object pointer
        """
        journal_obj = self.env['account.move']
        transaction_rec_list = []
        for record in self:
            if record.txn_type == 'receive':
                transaction_rec_list.append((0, 0,
                             {
                                 'account_id': record.journal_id.default_debit_account_id.id,
                                 'debit': record.total_amount,
                                 'credit': 0.0
                             }))
                for rec in record.txn_line_ids:
                    transaction_rec_list.append((0, 0,
                                 {
                                     'account_id': rec.account_id.id,
                                     'debit': 0.0,
                                     'credit': rec.amount
                                 }))
            elif record.txn_type == 'send':
                transaction_rec_list.append((0, 0,
                             {
                                 'account_id': record.journal_id.default_credit_account_id.id,
                                 'credit': record.total_amount,
                                 'debit': 0.0
                             }))
                for rec in record.txn_line_ids:
                    transaction_rec_list.append((0, 0,
                                 {
                                     'account_id': rec.account_id.id,
                                     'debit': rec.amount,
                                     'credit': 0.0
                                 }))
            vals = {
                'type': 'entry',
                'ref': record.ref,
                'date': record.date,
                'journal_id': record.journal_id.id,
                'line_ids': transaction_rec_list
            }
            Journal_rec = journal_obj.create(vals)
            Journal_rec.action_post()
            record.move_id = Journal_rec.id

            for transaction in record:
                transaction.state = 'posted'

    def cancel(self):
        """
        This method is used for changing the state to 'CANCEL'.
        And its related journal entry will be in the canceled state.
        --------------------------------------------------------
        @param self: object pointer
        """
        for transaction in self:
            transaction.state = 'canceled'
            transaction.move_id.write({
                'state': 'cancel'
            })

    def unlink(self):
        """
        Overridden unlink method to avoid deleting posted transactions
        --------------------------------------------------------------
        @param self: object pointer
        :return:
        """
        if self.state == 'posted':
            raise UserError(_("Posted Transactions can not be deleted!"))
        return super(AccountTransaction, self).unlink()


class AccountTransactionLines(models.Model):
    _name = 'account.transaction.line'

    txn_id = fields.Many2one('account.transaction', 'transaction')
    account_id = fields.Many2one('account.account', string='Account', required=True)
    currency_id = fields.Many2one('res.currency', related='txn_id.currency_id', string='Currency')
    amount = fields.Monetary('Amount', required=True)
    name = fields.Char(string='Description')
