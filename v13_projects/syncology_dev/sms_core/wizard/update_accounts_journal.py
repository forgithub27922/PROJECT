from odoo import api, fields, models, _


class UpdateAccountWizard(models.TransientModel):
    _name = "update.account.wizard"
    _description = "Update Account wizard"

    from_account = fields.Many2one('account.account', 'From Account')
    to_account = fields.Many2one('account.account', 'To Account')
    journal_id = fields.Many2one('account.journal', 'Journal')

    def update_account(self):
        """
        This method will be used to update From Account, To Account and Journal on insatallment
        ----------------------------------------------------------------------------------------
        @param self: object pointer
        """
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('active_id'))
        vals = {'from_account': self.from_account, 'to_account': self.to_account, 'journal_id': self.journal_id}
        fee_policy_line.write(vals)

    @api.model
    def default_get(self, fields_list):
        """
        Overridden default_get method to add additional field's default value.
        ----------------------------------------------------------------------
        @param self: object pointer
        @param fields_list: List of fields
        :return: A dictionary containing fields and their default values
        """
        res = super(UpdateAccountWizard, self).default_get(fields_list)
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('active_id'))
        res.update({
            'from_account': fee_policy_line.from_account.id,
            'to_account': fee_policy_line.to_account.id,
            'journal_id': fee_policy_line.journal_id.id,
        })
        return res

