# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo import models, api


class AccountTrialBalanceReport(models.AbstractModel):
    _name = 'report.bista_account_report.acc_trial_bal_rept_main'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        account_data = []
        empty_partner = []
        dates_info = {'date_from':data.get('date_from'),'date_to':data.get(
            'date_to')}
        account_info = {'code':'', 'acc_name':''}
        account_id = False
        for rec in docs:
            account_id = rec.account_id
            if not account_id.code in account_info.get('code'):
                account_info.update({'code':account_id.code,
                                     'acc_name':account_id.name})
            self._cr.execute("""select * from ((SELECT COALESCE(sum(aml.balance),'0'),aml.partner_id
                                FROM account_move_line aml
                                WHERE company_id = %s  AND
                                aml.account_id = %s AND aml.date <
                                %s GROUP by aml.account_id, aml.partner_id)
                                 as total_account FULL OUTER JOIN
                                 (SELECT COALESCE(sum(aml.debit),'0'),
                                 COALESCE(sum(aml.credit),'0'),
                                 aml.partner_id
                                FROM account_move_line aml WHERE company_id =
                                %s AND aml.account_id = %s
                                and aml.date >= %s and aml.date <= %s GROUP
                                by aml.account_id,
                                aml.partner_id) as dates ON
                                total_account.partner_id =
                                dates.partner_id);""",
                             (rec.company_id.id, account_id.id,data.get(
                                 'date_from'),rec.company_id.id,
                              account_id.id,data.get('date_from'),data.get(
                                 'date_to'),))
            query_res = self._cr.fetchall()
            if query_res:
                for rec in query_res:
                    if rec[1] == None and rec[4] == None:
                        empty_partner.append(tuple(rec))
                    else:
                        account_data.append(tuple(rec))
                account_data.extend(empty_partner)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'dates_info':dates_info,
            'account_info':account_info,
            'account_data': account_data
        }
