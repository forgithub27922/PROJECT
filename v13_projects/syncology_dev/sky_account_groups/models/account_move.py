from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = "account.move"

    global_id = fields.Char(readonly=True, string='Entry ID')

    def post(self):
        """
        Overridden action_post() method to change the sequence on the journal entries for Global ID field.(account.move)
        ----------------------------------------------------------------------------------------------------------------
        :return: it returns a Boolean.
        """
        acc_move_res = super(AccountMove, self).post()
        if not self.global_id:
            seq_journal = self.env.ref('sky_account_groups.sequence_journal')
            for record in self:
                record.global_id = seq_journal.next_by_id()
        return acc_move_res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    global_id = fields.Char(related='move_id.global_id', store=True, string='Entry ID')
    group_id = fields.Many2one('account.group', related='account_id.group_id', store=True)
