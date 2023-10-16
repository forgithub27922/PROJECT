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


class ReportVatFta(models.AbstractModel):
    _name = 'report.bista_account_report.bista_account_report_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        account_data = {}
        account_ids = False
        for rec in docs:
            if not rec.account_ids:
                account_ids = self.env['account.account'].search([('company_id', '=', rec.company_id.id)])
            else:
                account_ids = rec.account_ids
            for accounts in account_ids:
                if accounts not in account_data:
                    account_data.update({accounts: []})
                self._cr.execute("""SELECT sum(aml.debit),sum(aml.credit),aml.partner_id
                                    FROM account_move_line aml
                                    WHERE aml.partner_id is not Null AND aml.account_id in %s
                                    AND aml.date >= %s and aml.date <= %s
                                    GROUP by aml.account_id,aml.partner_id""" , (tuple([accounts.id]),data.get('date_from'),data.get('date_to'),))
                query_res = self._cr.fetchall()
                if query_res:
                    account_data[accounts].extend(query_res)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'account_data': account_data
        }

