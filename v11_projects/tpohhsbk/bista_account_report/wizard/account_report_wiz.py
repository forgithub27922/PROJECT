# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountReportWiz(models.TransientModel):
    _name = 'account.report.wiz'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    account_ids = fields.Many2many(
        'account.account', 'rel_rept_acc', 'rept_id', 'acc_id', 'Accounts')


    @api.multi
    def print_report(self, data):
        '''
            This method will print report.
        '''
        start_date = end_date = False
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    _('End date should be greater than start date.'))
            else:
                start_date = self.start_date
                end_date = self.end_date


        elif not self.start_date and not self.end_date:
            start_date = datetime.today().replace(day=1).date()
            end_date = start_date + relativedelta(days=-1, months=+1)

        elif self.end_date and not self.start_date:
            start_date = datetime.today().replace(day=1).date()
            end_date = self.end_date
        elif self.start_date and not self.end_date:
            start_date = self.start_date
            end_date = datetime.today().replace(day=1).date() + relativedelta(days=-1, months=+1)

        data = {}
        data['form'] = self.read([])
        data.update({'date_from':start_date,'date_to':end_date})
        return self.env.ref('bista_account_report.action_report_account'
                            ).report_action(self.ids, data=data, config=False)
