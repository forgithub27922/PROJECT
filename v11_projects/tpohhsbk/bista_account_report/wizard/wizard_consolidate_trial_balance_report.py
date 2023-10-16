# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


import base64
import xlsxwriter
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime,date
from odoo.tools.misc import formatLang
from odoo.exceptions import ValidationError


class wizard_consolidate_trial_bs_report(models.TransientModel):
    _name ='wizard.consolidate.trial.bs.report'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one('res.company',string="Company",
                                default=lambda self: self.env.user.company_id)
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='Status', readonly=True, default='init')
    name = fields.Char('File Name')
    file_download = fields.Binary('File to Download')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validation on dates"""
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(
                    'End Date must be greater than Start Date!'
                )

    @api.multi
    def print_xls_report(self):
        workbook = xlsxwriter.Workbook('consolidated_trial_balance_report.xls')
        worksheet = workbook.add_worksheet('Consolidated Trial Balance')

        trial_balance_report_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':20})

        statement_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':12, \
                                                'num_format':'dd/mm/yy'})

        date_statement_merge_format = workbook.add_format({'bold':True,'valign':'vcenter','font_size':9, \
                                                'num_format':'dd/mm/yy'})

        header_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':10,'border':1})

        data_format = workbook.add_format({'align':'center','valign':'vcenter','font_size':9})
        analytic_data_format = workbook.add_format({'valign':'vcenter','font_size':10,'bold':1})

        worksheet.merge_range(1, 0, 1, 5, self.company_id.name,statement_merge_format)
        worksheet.merge_range(3, 0, 4, 4, "Trial Balance - Cost Center",trial_balance_report_merge_format)

        start_date = datetime.strptime(self.start_date,'%Y-%m-%d').strftime("%d-%b-%y")
        end_date = datetime.strptime(self.end_date,'%Y-%m-%d').strftime("%d-%b-%y")

        worksheet.merge_range(3, 5, 4, 5, "Date",statement_merge_format)
        worksheet.merge_range(3, 6, 4, 6, start_date + " To " + end_date,date_statement_merge_format)

        worksheet.set_column('A:A',14)
        worksheet.set_column('B:B',24)
        worksheet.set_column('C:G',14)
        worksheet.write(7,0,'Acc. #',header_merge_format)
        worksheet.write(7,1,'A/c Name',header_merge_format)
        worksheet.write(7,2,'Opening Balance',header_merge_format)
        worksheet.write(7,3,'Debit',header_merge_format)
        worksheet.write(7,4,'Credit',header_merge_format)
        worksheet.write(7,5,'Change',header_merge_format)
        worksheet.write(7,6,'Closing Balance',header_merge_format)

        analytic_account_ids = self.env['account.analytic.account'].sudo().search([('company_id','=',self.company_id.id),
        ('line_ids', '!=', False)],order='sequence')
        if not analytic_account_ids:
            raise Warning(_("No Cost Center Transaction Found for company %s !") % (self.company_id.name))
        rows = 10
        column = 0

        assets_type_obj = self.env['account.account.type'].sudo()
        assets_type_obj |= self.env.ref('account.data_account_type_receivable')
        assets_type_obj |= self.env.ref('account.data_account_type_liquidity')
        assets_type_obj |= self.env.ref('account.data_account_type_current_assets')
        assets_type_obj |= self.env.ref('account.data_account_type_non_current_assets')
        assets_type_obj |= self.env.ref('account.data_account_type_fixed_assets')
        assets_type_obj |= self.env.ref('account.data_account_type_equity')

        liabilities_type_obj = self.env['account.account.type'].sudo()
        liabilities_type_obj |= self.env.ref('account.data_account_type_current_liabilities')
        liabilities_type_obj |= self.env.ref('account.data_account_type_non_current_liabilities')
        liabilities_type_obj |= self.env.ref('account.data_account_type_payable')

        income_type_obj = self.env['account.account.type'].sudo()
        income_type_obj |= self.env.ref('account.data_account_type_other_income')
        income_type_obj |= self.env.ref('account.data_account_type_revenue')

        expenses_type_obj = self.env.ref('account.data_account_type_expenses')
        account_type_data = {1:'Assets',2:'Liability',3:'Income',4:'Expense'}
        account_type_wise_dict = {1:assets_type_obj,2:liabilities_type_obj,
                                  3:income_type_obj,4:expenses_type_obj}

        analytic_account_dict = {}
        for account_key,account_value in sorted(account_type_wise_dict.items(),key=lambda key: key):
            analytic_account_ids = self.get_analytic_account(account_value)
            if analytic_account_ids:
                analytic_account_dict.setdefault(account_key,{})
                analytic_account_ids = [x[0] for x in analytic_account_ids]
                analytic_account_ids = self.env['account.analytic.account'].sudo().browse(analytic_account_ids)
                for analytic_acc in analytic_account_ids:
                    analytic_account_dict[account_key].setdefault(analytic_acc,[])
                    account_data = self.get_analytic_acc_wise_account(analytic_acc,account_value)
                    for each in account_data:
                        account_id = self.env['account.account'].sudo().browse(each[0])
                        opening_balance = debit = credit = balance = 0.00
                        options = {}
                        group_acc = self.env['account.general.ledger'].sudo().with_context(
                                    date_from_aml=self.start_date,
                                    date_to=self.end_date,
                                    company_ids=[self.company_id.id],
                                    state='posted',
                                    analytic_account_ids = analytic_acc,
                                    date_from=self.start_date and
                                    self.company_id.compute_fiscalyear_dates(
                                        datetime.strptime(self.start_date, "%Y-%m-%d")
                                )['date_from'] or None).group_by_account_id(options, account_id.id)
                        if group_acc:
                            debit = sum(group_acc[account_id]['lines'].mapped('debit'))
                            credit = sum(group_acc[account_id]['lines'].mapped('credit'))
                            balance = group_acc[account_id]['debit'] - group_acc[account_id]['credit']
                            opening_balance = group_acc[account_id]['initial_bal']['balance']

                        if opening_balance or credit or debit or balance:
                            analytic_account_dict[account_key][analytic_acc].append(({'code':account_id.code,'name':account_id.name,
                            'opening_balance':opening_balance,'debit':debit,'credit':credit,'balance':balance}))
        for account_type_key,account_type_value in analytic_account_dict.items():
            worksheet.write(rows,column,account_type_data[account_type_key],analytic_data_format)
            rows +=1
            group_total_opening_balance = group_total_debit = group_total_credit = group_total_change = group_total_balance = 0.00
            for key,value in sorted(account_type_value.items(),key=lambda key: key[0].sequence):
                worksheet.write(rows,column,key.name,analytic_data_format)
                rows+=1
                total_opening_balance = total_debit = total_credit = total_change = total_balance = 0.00

                for lines in value:
                    opening_bal = lines['opening_balance']
                    line_balance = lines['balance']
                    account_id = self.env['account.account'].sudo().search([('code','=',lines['code']),
                                                                            ('company_id','=',self.company_id.id)], limit=1)

                    if account_id and account_id.is_retained_earning:
                        opening_bal = self.get_retained_earning_amount(
                            lines['opening_balance'])
                        line_balance = opening_bal - (lines['debit'] - lines['credit'])

                    worksheet.write(rows,column,lines['code'],data_format)
                    worksheet.write(rows,column+1,lines['name'],data_format)
                    worksheet.write(rows,column+2,formatLang(self.env,opening_bal),data_format)
                    worksheet.write(rows,column+3,formatLang(self.env,lines['debit']),data_format)
                    worksheet.write(rows,column+4,formatLang(self.env,lines['credit']),data_format)
                    worksheet.write(rows,column+5,formatLang(self.env,lines['debit'] - lines['credit']),data_format)
                    worksheet.write(rows,column+6,formatLang(self.env,line_balance),data_format)
                    total_opening_balance += opening_bal
                    total_debit += lines['debit']
                    total_credit += lines['credit']
                    total_balance += line_balance
                    total_change += lines['debit'] - lines['credit']
                    rows+=1

                rows+=1
                worksheet.write(rows,column+1,key.name + " Total",analytic_data_format)
                worksheet.write(rows,column+2,formatLang(self.env,total_opening_balance),data_format)
                worksheet.write(rows,column+3,formatLang(self.env,total_debit),data_format)
                worksheet.write(rows,column+4,formatLang(self.env,total_credit),data_format)
                worksheet.write(rows,column+5,formatLang(self.env,total_change),data_format)
                worksheet.write(rows,column+6,formatLang(self.env,total_balance),data_format)
                rows +=2

                group_total_opening_balance +=total_opening_balance
                group_total_debit += total_debit
                group_total_credit += total_credit
                group_total_change += total_change
                group_total_balance += total_balance

            worksheet.write(rows,column+1,account_type_data[account_type_key] + " Total",analytic_data_format)
            worksheet.write(rows,column+2,formatLang(self.env,group_total_opening_balance),data_format)
            worksheet.write(rows,column+3,formatLang(self.env,group_total_debit),data_format)
            worksheet.write(rows,column+4,formatLang(self.env,group_total_credit),data_format)
            worksheet.write(rows,column+5,formatLang(self.env,group_total_change),data_format)
            worksheet.write(rows,column+6,formatLang(self.env,group_total_balance),data_format)
            rows +=2

        workbook.close()

        self.write({
            'state': 'done',
            'file_download': base64.b64encode(open('consolidated_trial_balance_report.xls','rb').read()),
            'name': 'consolidated_trial_balance_report.xls'
        })

        return {
            'name': 'Consolidated Trial Balance Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def get_retained_earning_amount(self, opening_balance):
        """Calculate unallocated retained earning amount in TB report."""
        unallocated_retained_earning_amount = 0.00
        equity_line = self.env.ref(
            'account_reports.account_financial_previous_year_earnings0').sudo()
        balance_sheet_financial_report = self.env.ref(
            'account_reports.account_financial_report_balancesheet0').sudo()
        linesDict = {}
        currency_table = {}
        get_balance = equity_line.sudo().with_context(date_to=self.end_date,
                                                      state='posted',
                                                      company_ids=
                                                      self.company_id.ids
                                                      ).get_balance(
            linesDict, currency_table, balance_sheet_financial_report,
            ['balance'])
        if get_balance:
            unallocated_retained_earning_amount = get_balance[0]['balance']
        return unallocated_retained_earning_amount - opening_balance

    @api.multi
    def do_go_back(self):
        self.state = 'init'
        return {
            'name': 'Consolidated Trial Balance Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def get_analytic_account(self,account_type):
        '''
            This Function used to find the analytic account for given date range with specific account type.
        '''
        # start_date = datetime.strptime(self.start_date,"%Y-%m-%d").date()
        # start_date = start_date.replace(month=1, day=1)
        # fiscalyear_lock_date = self.company_id.fiscalyear_lock_date
        # start_date= self.company_id.compute_fiscalyear_dates(
        #                                 datetime.strptime(self.start_date, "%Y-%m-%d"))['date_from'] or None

        params = (self.company_id.id,tuple(account_type.ids))
        query = """ SELECT
                        DISTINCT(aml.analytic_account_id)
                    FROM account_move_line aml
                    LEFT JOIN account_move move on
                    move.id=aml.move_id
                    WHERE aml.company_id = %s
                    AND aml.analytic_account_id is not null
                    AND move.state = 'posted'
                    AND aml.user_type_id in %s
                    GROUP BY aml.analytic_account_id
                """
        self.env.cr.execute(query,params=params)
        qry_res = self._cr.fetchall()
        return qry_res

    def get_analytic_acc_wise_account(self,analytic_acc,account_type):
        '''
            This Function used to find the account for given date range with specific account type and analytic account.
        '''
        # start_date = datetime.strptime(self.start_date,"%Y-%m-%d").date()
        # start_date = start_date.replace(month=1, day=1)
        # start_date= self.company_id.compute_fiscalyear_dates(
        #                                 datetime.strptime(self.start_date, "%Y-%m-%d"))['date_from'] or None
        # fiscalyear_lock_date = self.company_id.fiscalyear_lock_date
        params = (self.company_id.id,analytic_acc.id,tuple(account_type.ids))
        query = """ SELECT
                        aml.account_id
                    FROM account_move_line aml
                    LEFT JOIN account_move move on
                    move.id=aml.move_id
                    WHERE aml.company_id=%s
                    AND aml.analytic_account_id is not null
                    AND move.state = 'posted'
                    AND aml.analytic_account_id = %s
                    AND aml.user_type_id in %s
                    GROUP BY aml.account_id
                """
        self.env.cr.execute(query,params=params)
        qry_res = self._cr.fetchall()
        return qry_res
