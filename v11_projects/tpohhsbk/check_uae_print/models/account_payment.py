from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Account_Payment(models.Model):
    _inherit = 'account.payment'

    check_format_id = fields.Many2one('cheque.format', string="Cheque Format", compute="get_cheque_format_id")
    land_lord_id = fields.Many2one('res.partner', 'Land Lord')

    @api.depends('journal_id')
    def get_cheque_format_id(self):
        for each in self:
            if each.journal_id.account_checkbook_id:
               each.check_format_id = each.journal_id.account_checkbook_id.cheque_format_id.id

    @api.multi
    def do_print_checks(self):
        us_check_layout = self[0].company_id.us_check_layout
        if us_check_layout != 'disabled':
            self.write({'state': 'sent'})
            if self._context and self.journal_id.account_checkbook_id:
#                 and self._context.get('default_next_check_number')
                if self.journal_id.account_checkbook_id.printed_page == 0:
                    next_page = self.journal_id.account_checkbook_id.start_page
                else:
                    next_page = self.journal_id.account_checkbook_id.printed_page + 1

                if next_page > self.journal_id.account_checkbook_id.pages:
                    raise UserError(_("Not enough cheque. Please define new cheque Book"))

                self.journal_id.account_checkbook_id.printed_page = next_page

                self = self.with_context(default_next_check_number=next_page)

            return self.env.ref('check_uae_print.action_print_uae_cheque').report_action(self)
        return super(Account_Payment, self).do_print_checks()

    @api.multi
    def print_checks(self):
        res = super(Account_Payment, self).print_checks()
        """ set 'next check number' based on specific checkbook/journal """
        if res.get('context') and res.get('context').get('default_next_check_number') and self.journal_id.account_checkbook_id:

            if self.journal_id.account_checkbook_id.printed_page == 0:
                next_page = self.journal_id.account_checkbook_id.start_page
            else:
                next_page = self.journal_id.account_checkbook_id.printed_page + 1
            if next_page > self.journal_id.account_checkbook_id.pages:
                raise UserError(_("Not enough cheque. Please define new cheque Book"))

            # self.journal_id.account_checkbook_id.printed_page = next_page
            res['context'].update({'default_next_check_number':next_page})
        return res