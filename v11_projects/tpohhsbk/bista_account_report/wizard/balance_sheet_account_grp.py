# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from datetime import datetime, date


class wizard_balance_sheet_account_grp(models.TransientModel):
    _name = 'wizard.balance.sheet.account.grp'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    date = fields.Date(string='Date', default=date.today())
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')


    def domain_of_acc_grp(self):

        fixed_asset_grp = self.env.ref('sbk_group.account_group_main_1')
        curr_ass_loan = self.env.ref('sbk_group.account_group_main_3')
        non_current_laib = self.env.ref('sbk_group.account_group_main_4')
        current_laib_grp = self.env.ref('sbk_group.account_group_main_5')
        equity_grp = self.env.ref('sbk_group.account_group_main_6')
        investment_grp = self.env.ref('sbk_group.account_group_main_2')

        grps = fixed_asset_grp + curr_ass_loan + non_current_laib + current_laib_grp + equity_grp + investment_grp

        return [('id', 'in', grps.ids)]

    acc_group_ids = fields.Many2many('account.group', string="Group")# ,domain=domain_of_acc_grp




    @api.multi
    def print_report(self):
        '''
            This method will print report.
        '''
        data = {}
        data['form'] = self.read([])
        return self.env.ref('bista_account_report.action_report_balance_sheet_acc_grp').\
                        report_action(self.ids, data=data)
