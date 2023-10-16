# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo.modules.module import get_module_path
from datetime import datetime,date
from odoo.tools.misc import formatLang
import base64
import xlsxwriter


class wizard_consolidate_report_wizard(models.TransientModel):
    _name ='wizard.consolidate.report'

    end_date = fields.Date(string="Date")
    company_ids = fields.Many2many('res.company',string="Company")
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='Status', readonly=True, default='init')
    name = fields.Char('File Name')
    file_download = fields.Binary('File to Download')

    @api.multi
    def print_xls_report(self):
        workbook = xlsxwriter.Workbook('bank_consolidated_report.xls')
        worksheet = workbook.add_worksheet('Bank Balance')
        bank_balance_merge_format = workbook.add_format({'bold':True,'align':'center','underline': 1,'valign':'vcenter', \
                                            'font_size':32})
        bank_balance_report_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':20})

        statement_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':12, \
                                                'num_format':'dd/mm/yy'})

        header_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':10,'bg_color':'#808080','border':1})

        company_data_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':12,'bg_color':'#D3D3D3','border':1})

        data_format = workbook.add_format({'align':'center','valign':'vcenter','font_size':9,'border':1})

        module_path =get_module_path('bista_account_report')
        module_path += '/static/image/sbk_image.jpg'

        worksheet.insert_image(0,0,module_path)

        worksheet.merge_range(0, 0, 6, 10, "BANK BALANCES",bank_balance_merge_format)
        worksheet.merge_range(8, 2, 9, 5, "Bank Balance Report",bank_balance_report_merge_format)

        date = datetime.strptime(self.end_date,'%Y-%m-%d').strftime("%d-%b-%y")
        worksheet.merge_range(8, 7, 9, 8, "Statement Date",statement_merge_format)
        worksheet.merge_range(8, 9, 9, 10, date,statement_merge_format)

        if self.company_ids:
            company_ids = self.company_ids
        else:
            company_ids = self.env['res.company'].sudo().search([])

        missing_bank_acc_journal_lst = {}
        for company in company_ids:
            journal_ids = self.env['account.journal'].sudo().search([('type','=','bank'),('company_id','=',company.id),
            ('bank_account_id','=',False)])
            if journal_ids:
                missing_bank_acc_journal_lst.setdefault(company,[])
            for journal in journal_ids:
                missing_bank_acc_journal_lst[company].append(journal.name)

        if missing_bank_acc_journal_lst:
            tbody_template = "<b><p>Please Configure Bank account in Following Journal:</p></b>"
            for key,value  in missing_bank_acc_journal_lst.items():
                tbody_template += """ <p style="text-align: center;">
                                    <b> Company -  %s </b></p>""" % (key.name)
                tbody_template += """
                        <table class="table table-bordered"><tbody>
                    """
                td_count = 0
                tbody_template += """ <tr> """
                for each in value:
                    if td_count >4:
                        tbody_template += """ </tr> """
                        tbody_template += """ <tr> """
                        td_count = 0
    
                    tbody_template += """ 
                        <td> %s </td> """ %(each)
                    td_count +=1

                tbody_template += """ </tr></tbody></table> """

            return {
            'name': 'Bank Consolidated Report Missing Bank Account',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.bank.consolidate.error',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context':{'default_warning_html':tbody_template}
            }

        currency_ids = self.env['res.currency'].sudo().search([('active','=',True)])

        worksheet.set_column('B:D',28)
        worksheet.merge_range(10,0,12,0,'S No:',header_merge_format)
        worksheet.merge_range(10,1,12,1,'Name of the Bank & Branch',header_merge_format)
        worksheet.merge_range(10,2,12,2,'Account name',header_merge_format)
        worksheet.merge_range(10,3,12,3,'Account number',header_merge_format)

        bank_balance_column = 4+len(currency_ids)
        worksheet.merge_range(10,4,11,bank_balance_column-1,'Bank Balance',header_merge_format)

        # Overdraft limit
        worksheet.merge_range(10,bank_balance_column,11,bank_balance_column+len(currency_ids)-1,'Unutilized Over Draft',header_merge_format)

        row = 12
        column = 4
        dynamic_column_list = {}
        grand_total_dict = {}
        currency_wise_od_limit = {}

        # Overdraft limit
        od_dynamic_column_list = {}
        od_grand_total_dict = {}
        overdraft_column = bank_balance_column
        for currency in currency_ids:
            worksheet.write(row,column,currency.name,header_merge_format)
            grand_total_dict.setdefault(column,0.00)
            dynamic_column_list.setdefault(currency.id,column)

            # Overdraft limit 
            worksheet.write(row,overdraft_column,currency.name,header_merge_format)
            od_grand_total_dict.setdefault(overdraft_column,0.00)
            od_dynamic_column_list.setdefault(currency.id,overdraft_column)
            overdraft_column +=1
            currency_wise_od_limit.setdefault(currency.id,{})
            for company in company_ids:
                currency_wise_od_limit[currency.id].setdefault(company.id,0.00)
            column +=1

        row = 14
        worksheet.set_column(4,overdraft_column,12)
        for company in company_ids:
            worksheet.merge_range(row,0,row,column-1,company.name,company_data_merge_format)
            worksheet.merge_range(row,bank_balance_column,row,bank_balance_column+len(currency_ids)-1,'',company_data_merge_format)
            row+=1
            data = self.get_company_consolidate_report(company)
            count=1
            dynamic_column_total = {}
            od_dynamic_column_total = {}
            for key,value in data[0].items():
                if key.branch_id:
                    bank_name = key.bank_id.name + ' - ' + key.branch_id.name
                else:
                    bank_name = key.bank_id.name
                worksheet.write(row,0,count,data_format)
                worksheet.write(row,1,bank_name,data_format)
                worksheet.write(row,2,key.bank_account_id.partner_id.name,data_format)
                worksheet.write(row,3,key.bank_account_id.acc_number,data_format)

                for each_column in range(4,overdraft_column):
                    worksheet.write(row,each_column,0.00,data_format)

                amount = 0.00
                od_amount = 0.00
                dynamic_column = False
                od_dynamic_column = False
                currency_id = key.currency_id.id if key.currency_id else company.currency_id.id
                if value and value[0]:
                    amount = sum([float(x[1]) for x in value])
                    if key.currency_id:
                        amount = company.currency_id.with_context(date=self.end_date).compute(amount, key.currency_id)
                    else:
                        currency_id = value[0][0]

                if currency_id:
                    dynamic_column = dynamic_column_list[currency_id]
                    od_dynamic_column = od_dynamic_column_list[currency_id]

                # Overdraft limit
                if key.is_overdraft:
                    od_amount = key.overdraft_limit
                    if amount <= 0:
                        od_amount = key.overdraft_limit + amount
                        amount = 0.00

                    if od_dynamic_column and od_amount:
                        worksheet.write(row,od_dynamic_column,formatLang(self.env,od_amount),data_format)
                        od_dynamic_column_total.setdefault(od_dynamic_column,0.00)
                        od_dynamic_column_total[od_dynamic_column] +=od_amount
                        currency_wise_od_limit[currency_id][company.id] += od_amount

                if dynamic_column and amount:
                    dynamic_column_total.setdefault(dynamic_column,0.00)
                    if key.is_overdraft and amount < 0:
                        continue
                    worksheet.write(row,dynamic_column,formatLang(self.env,amount),data_format)
                    dynamic_column_total[dynamic_column] +=amount
                    
                count+=1
                row +=1
            row +=1
            worksheet.merge_range(row,0,row,3,'Total '  +company.name,company_data_merge_format)
            for each_column in range(4,overdraft_column):
                worksheet.write(row,each_column,0.00,company_data_merge_format)

            for key,value in dynamic_column_total.items():
                worksheet.write(row,key,formatLang(self.env,value),company_data_merge_format)
                grand_total_dict[key] += value

            # Overdraft limit
            for key,value in od_dynamic_column_total.items():
                worksheet.write(row,key,formatLang(self.env,value),company_data_merge_format)
                od_grand_total_dict[key] += value

            row +=2

        for currency in currency_ids:
            self.currency_wise_xls_report(currency,company_ids,workbook,currency_wise_od_limit)

        worksheet.merge_range(row,0,row,3,'Grand Total',company_data_merge_format)
        for key,value in grand_total_dict.items():
            worksheet.write(row,key,formatLang(self.env,value),company_data_merge_format)

        # Overdraft limit
        for key,value in od_grand_total_dict.items():
            worksheet.write(row,key,formatLang(self.env,value),company_data_merge_format)

        workbook.close()

        self.write({
            'state': 'done',
            'file_download': base64.b64encode(open('bank_consolidated_report.xls','rb').read()),
            'name': 'bank_consolidated_report.xls'
        })

        return {
            'name': 'Bank Consolidated Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def do_go_back(self):
        self.state = 'init'
        return {
            'name': 'Bank Consolidated Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.one
    def get_company_consolidate_report(self,company):
        journal_ids = self.env['account.journal'].sudo().search([('type','=','bank'),('company_id','=',company.id),
            ('bank_id','!=',False)])

        journal_wise_data = {}

        for journal in journal_ids:
            if not journal.default_debit_account_id:
                raise Warning(_('Please set Debit/Credit account in %s Journal for company %s') % (journal.name,company.name))

            journal_wise_data.setdefault(journal,[])

            currency_field = 'aml.company_currency_id'
            sum_of_amount = 'coalesce(sum(aml.debit-aml.credit),0)'
            currency_id = company.currency_id

            params = (company.id,self.end_date,journal.default_debit_account_id.id,
                      currency_id.id)
            query = """ SELECT
                         """ + currency_field +  """,
                         """ + sum_of_amount +  """
                        FROM account_move_line aml
                        LEFT JOIN account_move move on
                        move.id=aml.move_id
                        WHERE 
                        aml.company_id=%s
                        AND aml.date <=%s
                        AND aml.account_id = %s
                        AND  """ + currency_field + """ = %s
                        AND move.state = 'posted'
                        GROUP BY """ + currency_field + """
                    """
            self.env.cr.execute(query,params=params)
            qry_res = self._cr.fetchall()
            journal_wise_data[journal].extend(qry_res)

        return journal_wise_data

    def currency_wise_xls_report(self,currency,company_ids,workbook,currency_wise_od_limit):
        ''' 
            Currency Wise Consolidate  Report Add new Sheet in same workbook.
        '''
        currency_wise_grand_total = {}
        worksheet = workbook.add_worksheet('Consolidate ' + currency.name)

        bank_balance_merge_format = workbook.add_format({'bold':True,'align':'center','underline': 1,'valign':'vcenter', \
                                            'font_size':32})
        bank_balance_report_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':20})

        statement_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':12, \
                                                'num_format':'dd/mm/yy'})

        header_merge_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter', \
                                            'font_size':10,'border':1})

        data_format = workbook.add_format({'align':'center','valign':'vcenter','font_size':9,'border':1})


        module_path =get_module_path('bista_account_report')
        module_path += '/static/image/sbk_image.jpg'

        worksheet.insert_image(0,0,module_path)
        worksheet.merge_range(0, 0, 6, 10, "BANK BALANCES",bank_balance_merge_format)
        worksheet.merge_range(8, 2, 9, 5, 'Currency - ' + currency.name ,bank_balance_report_merge_format)
        date = datetime.strptime(self.end_date,'%Y-%m-%d').strftime("%d-%b-%y")
        worksheet.merge_range(8, 9, 9, 10, date,statement_merge_format)

        journal_ids = self.env['account.journal'].sudo().search([('type','=','bank'),('company_id','in',company_ids.ids),
            ('bank_id','!=',False)])

        worksheet.set_column('B:B',28)
        worksheet.merge_range(10,0,12,0,'S No:',header_merge_format)
        worksheet.merge_range(10,1,12,1,'Company',header_merge_format)

        account_journal_ids = self.env['account.journal'].sudo()
        total_account_journal_ids = self.env['account.journal'].sudo()
        for company in company_ids:
            company_journal_ids = journal_ids.filtered(lambda l:l.company_id.id == company.id)
            total_account_journal_ids |= company_journal_ids 

            if not currency or currency.id == company.currency_id.id:
                company_journal_ids = company_journal_ids.filtered(lambda l:not l.currency_id or l.currency_id.id == company.currency_id.id)
                account_journal_ids |= company_journal_ids
            else:
                company_journal_ids = company_journal_ids.filtered(lambda l:l.currency_id.id == currency.id)
                account_journal_ids |= company_journal_ids

        final_journal_ids = total_account_journal_ids & account_journal_ids

        journal_ids = final_journal_ids
        dynamic_column_list = {}
        currency_wise_grand_total = {}
        column = 2
        res_bank_ids = self.env['res.bank'].sudo()
        for journal in journal_ids:
            res_bank_ids |= journal.bank_id

        for bank in res_bank_ids:
            worksheet.merge_range(10,column,12,column,bank.name,header_merge_format)
            dynamic_column_list.setdefault(bank.id,column)
            currency_wise_grand_total.setdefault(column,0)
            column +=1

        #Overdraft limit
        unutilised_od_column = column
        worksheet.merge_range(10,column,12,column,'Unutilised Over Draft',header_merge_format)
        overdraft_column_total = {}
        overdraft_column_total.setdefault(column,0)

        column +=1

        worksheet.merge_range(10,column,12,column,'Total',header_merge_format)
        currency_wise_grand_total.setdefault(column,0)
        worksheet.set_column(2,column,22)

        currency_final_total_od_ammount = 0.00
        count=1
        row = 13
        for company in company_ids:
            worksheet.write(row,0,count,data_format)
            worksheet.write(row,1,company.name,data_format)
            journal_bank_data = self.journal_wise_bank_data(company,journal_ids,currency)
            for each_column in range(2,column):
                worksheet.write(row,each_column,'',data_format)

            total_amount = 0.00
            for key,value in journal_bank_data.items():
                amount = sum([float(x[0]) for x in value])
                if currency.id != company.currency_id.id:
                    amount = company.currency_id.with_context(date=self.end_date).compute(amount, currency)

                dynamic_column = dynamic_column_list[key.id]
                worksheet.write(row,dynamic_column,formatLang(self.env,amount),data_format)
                currency_wise_grand_total[dynamic_column] += amount
                total_amount += amount

            #Overdraft limit
            branch_wise_currency_total = currency_wise_od_limit[currency.id].get(company.id,0.00)
            if total_amount < 0:
                total_amount += branch_wise_currency_total
            else:
                total_amount -= branch_wise_currency_total

            worksheet.write(row,column,formatLang(self.env,total_amount),data_format)
            currency_wise_grand_total[column] += total_amount

            #Overdraft limit
            worksheet.write(row,unutilised_od_column,formatLang(self.env,branch_wise_currency_total),data_format)
            currency_final_total_od_ammount += branch_wise_currency_total

            count+=1
            row+=1

        worksheet.write(row+1,1,"Total",data_format)
        for key,value in currency_wise_grand_total.items():
            worksheet.write(row+1,key,formatLang(self.env,value),data_format)

        #Overdraft limit
        worksheet.write(row+1,unutilised_od_column,formatLang(self.env,currency_final_total_od_ammount),data_format)

    def journal_wise_bank_data(self,company,company_journal_ids,currency_id):
        journal_wise_data = {}
        for journal in company_journal_ids:
            if not journal.default_debit_account_id:
                raise Warning(_('Please set Debit/Credit account in %s Journal') % (journal.name))

            journal_wise_data.setdefault(journal.bank_id,[])
            currency_field = 'aml.company_currency_id'
            sum_of_amount = 'coalesce(sum(aml.debit-aml.credit),0)'    

            params = (company.id,self.end_date,journal.default_debit_account_id.id,
                      company.currency_id.id)
            query = """ SELECT
                         """ + sum_of_amount + """
                        FROM account_move_line aml
                        LEFT JOIN account_move move on
                        move.id=aml.move_id
                        WHERE
                        aml.company_id=%s
                        AND aml.date <=%s
                        AND aml.account_id = %s
                        AND  """ + currency_field + """ = %s
                        AND move.state = 'posted'
                        GROUP BY """ + currency_field + """
                    """
            self.env.cr.execute(query,params=params)
            qry_res = self._cr.fetchall()
            journal_wise_data[journal.bank_id].extend(qry_res)

        return journal_wise_data


class wizard_bank_consolidate_error(models.TransientModel):
    _name = 'wizard.bank.consolidate.error'

    warning_html = fields.Html(string="Warning")

