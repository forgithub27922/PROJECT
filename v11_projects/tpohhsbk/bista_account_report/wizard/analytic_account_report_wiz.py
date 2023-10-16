# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from datetime import datetime, date


class analytic_account_report_wiz(models.TransientModel):
    _name = 'analytic.account.report.wiz'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    date = fields.Date(string='Date', default=date.today())
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    @api.multi
    def print_report(self):
        '''
            This method will print report.
        '''
        data = {}
        data['form'] = self.read([])
        data['date'] = self.date
        return self.env.ref('bista_account_report.action_report_account_analytic').\
                        report_action(self.ids, data=data)


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    analytic_acc_group_id = fields.Many2one('analytic.group', related="analytic_account_id.analytic_group_id", string="Analytic Account Group", store=True, copy=False)

    my_acc_group_id = fields.Many2one('account.group', related="account_id.group_id", string="My  Account Group", store=True, copy=False)


class account_group(models.Model):
    _inherit = 'account.group'

    display_in_bs_report = fields.Boolean(string="Display in BS Report")
    highlighted_in_bs_report = fields.Boolean(string="Highlight in BS Report")