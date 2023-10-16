# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.modules.module import get_module_path
from datetime import datetime
import base64
import xlsxwriter
from odoo.tools.misc import formatLang


class wizard_pnl_consolidate_report_wizard(models.TransientModel):
    _name = 'wizard.pnl.consolidate.report'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_ids = fields.Many2many('res.company', string="Company")
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='Status', readonly=True, default='init')
    name = fields.Char('File Name')
    file_download = fields.Binary('File to Download')

    # Account Group Global Data
    group_row = 14
    space = 2
    group_dynamic_column_list = {}
    group_grand_total_dict = {}
    group_company_dynamic_column_list = {}

    # Account Account Global Data
    account_row = 14
    account_space = 2
    account_dynamic_column_list = {}
    account_grand_total_dict = {}
    account_company_dynamic_column_list = {}

    def find_parent_group(self, group_id):
        """
            Recursive Function which return parent account group.
            :param group_id: get recordset
            :return: recordset
        """
        acc_hrp_id = self.env['account.group'].search([('id', '=', group_id.parent_id.id)], limit=1)
        if acc_hrp_id:
            return self.find_parent_group(acc_hrp_id)
        else:
            return group_id

    @api.multi
    def print_xls_report(self):
        """
            Generate XLS consolidate balance sheet report.
            :return:
        """
        workbook = xlsxwriter.Workbook('profit_loss_consolidated_report.xls')

        # Create Main Group-> Sub Group-> Balance.
        self.account_grp_wise_xls_report(workbook)

        self.account_dynamic_column_list = {}
        self.account_grand_total_dict = {}
        self.account_company_dynamic_column_list = {}

        worksheet = workbook.add_worksheet('Group With Account Report')
        bank_balance_merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'underline': 1, 'valign': 'vcenter', \
             'font_size': 32})
        bank_balance_report_merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', \
                                                                'font_size': 8, 'bg_color': '#808080'})
        statement_merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 10, \
             'num_format': 'dd/mm/yy'})
        header_merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', \
                                                   'font_size': 10, 'border': 1})
        main_group_data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'font_size': 9, 'bold': True})
        amount_main_group_data_format = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'font_size': 9, 'bold': True})

        group_total_data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'font_size': 9, 'bold': True, 'bg_color': '#808080'})
        amount_group_total_data_format = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'font_size': 9, 'bold': True, 'bg_color': '#808080'})

        module_path = get_module_path('bista_account_report')
        module_path += '/static/image/sbk_image.jpg'

        worksheet.insert_image(0, 0, module_path)

        name = "OFFICE AND PALACE OF HH DR.SHEIKH SULTAN BIN KHALIFA BIN ZAYED AL NAHYAN" + "\n" \
               + "CONSOLIDATED PROFIT LOSS AS ON " + datetime.strptime(self.end_date, '%Y-%m-%d').strftime("%d-%B-%y")

        if self.company_ids:
            company_ids = self.company_ids
        else:
            company_ids = self.env['res.company'].sudo().search([])

        merge_end_no = len(company_ids.ids) + 1
        worksheet.merge_range(0, 0, 5, 2, "", bank_balance_merge_format)
        worksheet.merge_range(8, 0, 9, merge_end_no, name, bank_balance_report_merge_format)
        worksheet.merge_range(4, 3, 4, 5, "All Amount in AED", statement_merge_format)
        worksheet.set_column(0, len(company_ids), 20)
        worksheet.write(12, 0, 'Details', header_merge_format)
        row = 12
        column = 1
        pnl_data = {}
        for company in company_ids:
            worksheet.write(row, column, company.name, header_merge_format)
            self.account_grand_total_dict.setdefault(column, 0.00)
            self.account_company_dynamic_column_list.setdefault(company.id, 0.00)
            self.account_dynamic_column_list.setdefault(company.id, column)
            pnl_data.setdefault(company.id, [])
            column += 1

        worksheet.write(row, column, "Total", header_merge_format)

        account_account_type_obj = self.common_account_type()
        account_grp_obj = self.common_account_group_obj(company_ids, account_account_type_obj)

        worksheet.set_column(1, column, 20)

        for main_grp in account_grp_obj:
            main_group_total = 0.00

            worksheet.write(self.account_row, 0, main_grp.name, main_group_data_format)
            self.account_row += 1
            worksheet_data = {'worksheet': worksheet, 'row': self.account_row,
                              'column': column,
                              'format': main_group_data_format, 'workbook': workbook}
            self.recursive_group(worksheet_data, company_ids, main_grp, account_account_type_obj, main_grp)
            self.account_row += 1

            worksheet.write(self.account_row, 0, "Total  " + main_grp.name, group_total_data_format)
            all_child_group_ids = self.env['account.group'].search([('parent_id', 'child_of', main_grp.id)])
            for company in company_ids:
                amount = self.group_wise_pnl_data(company, all_child_group_ids, account_account_type_obj)
                set_column = self.account_dynamic_column_list[company.id]
                amount = amount[0][0] if amount else 0.00
                pnl_data[company.id].append(abs(amount))
                worksheet.write(self.account_row, set_column, formatLang(self.env, abs(amount)),
                                amount_group_total_data_format)
                main_group_total += amount

            worksheet.write(self.account_row, column, formatLang(self.env, main_group_total),
                            amount_group_total_data_format)
            self.account_row += 2
        total_p_n_l = 0.0
        for company in company_ids:
            profit_loss = pnl_data[company.id][0] - pnl_data[company.id][1]
            set_column = self.account_dynamic_column_list[company.id]
            worksheet.write(self.account_row, set_column, formatLang(self.env, profit_loss),
                            amount_group_total_data_format)
            total_p_n_l += profit_loss
        col_tot = len(company_ids.ids) + 1
        worksheet.write(self.account_row, 0, 'Profit/Loss',
                        group_total_data_format)
        worksheet.write(self.account_row, col_tot, formatLang(self.env, total_p_n_l),
                        amount_group_total_data_format)
        self.group_dynamic_column_list = {}
        self.group_grand_total_dict = {}
        self.group_company_dynamic_column_list = {}
        workbook.close()

        self.write({
            'state': 'done',
            'file_download': base64.b64encode(open('profit_loss_consolidated_report.xls', 'rb').read()),
            'name': 'profit_loss_consolidated_report.xls'
        })

        return {
            'name': 'Profit N Loss Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def do_go_back(self):
        """
            Return wizard again from back button.
            :return:
        """
        self.state = 'init'
        return {
            'name': 'Profit Loss Consolidated Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def recursive_group(self, worksheet_data, company_ids, child_group, account_account_type_obj, main_grp):
        """
            Recursive Function which return set group wise account and it's value.
            :param company_ids: company recordset
            :param child_group: group recordset
            :param account_account_type_obj: account_type recordset
            :param main_grp: main group dictionary
            :return:
        """
        child_ids = self.env['account.group'].search([('parent_id', '=', child_group.id)])
        worksheet = worksheet_data['worksheet']
        data_format = worksheet_data['format']
        workbook = worksheet_data['workbook']
        column = worksheet_data['column']
        amount_data_format = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 9})
        account_data_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'font_size': 9})
        amount_main_group_data_format = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'font_size': 9, 'bold': True})
        account_obj = self.env['account.account'].sudo()

        for each in child_ids:
            group_total = 0.00
            find_level = self.check_group_level(each)
            worksheet.write(self.account_row, 0, each.name.rjust(len(each.name) + find_level * 2), data_format)
            all_child_group_ids = self.env['account.group'].search([('parent_id', 'child_of', each.id)])
            for company in company_ids:
                group_amount = self.group_wise_pnl_data(company, all_child_group_ids, account_account_type_obj)
                group_company_set_column = self.account_dynamic_column_list[company.id]
                group_amount = group_amount[0][0] if group_amount else 0.00
                if main_grp == self.env.ref('sbk_group.account_group_main_7') and group_amount != 0.0:
                    group_amount *= -1
                worksheet.write(self.account_row, group_company_set_column, formatLang(self.env, group_amount),
                                amount_main_group_data_format)
                group_total += group_amount

            worksheet.write(self.account_row, column, formatLang(self.env, group_total), amount_main_group_data_format)

            self.account_row += 1
            for company in company_ids:
                data = self.company_pnl_data(company, each, account_account_type_obj)
                for record in data:
                    account_id = account_obj.browse(record[0])
                    worksheet.write(self.account_row, 0,
                                    account_id.display_name.rjust(len(account_id.display_name) + find_level * 2),
                                    account_data_format)
                    set_column = self.account_dynamic_column_list[company.id]
                    amount = record[1] if record[1] else 0.00
                    if main_grp == self.env.ref('sbk_group.account_group_main_7') and amount != 0.0:
                        amount *= -1
                    worksheet.write(self.account_row, set_column, formatLang(self.env, amount), amount_data_format)
                    for key, value in self.account_dynamic_column_list.items():
                        if key != company.id:
                            worksheet.write(self.account_row, value, formatLang(self.env, 0), amount_data_format)
                    worksheet.write(self.account_row, column, formatLang(self.env, amount), amount_data_format)
                    self.account_row += 1
            self.recursive_group(worksheet_data, company_ids, each, account_account_type_obj, main_grp)

    def check_group_level(self, group):
        level = 0
        parent_id = group.parent_id
        while parent_id:
            level += 1
            parent_id = parent_id.parent_id
        return level

    @api.multi
    def recursive_account_wise_group(self, worksheet_data, company_ids, child_group, account_account_type_obj, main_grp,
                                     space):
        """
            Recursive Function which return set group wise it's value.
            :param company_ids: company recordset
            :param child_group: group recordset
            :param account_account_type_obj: account_type recordset
            :param main_grp: main group dictionary
            :return:
        """
        child_ids = self.env['account.group'].search([('parent_id', '=', child_group.id)])
        worksheet = worksheet_data['worksheet']
        data_format = worksheet_data['format']
        workbook = worksheet_data['workbook']
        column = worksheet_data['column']
        amount_data_format = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 9})

        for each in child_ids:
            find_level = self.check_group_level(each)
            worksheet.write(self.group_row, 0, each.name.rjust(len(each.name) + find_level * 2), data_format)
            all_child_group_ids = self.env['account.group'].search([('parent_id', 'child_of', each.id)])
            child_group_total = 0.00

            for company in company_ids:
                amount = self.group_wise_pnl_data(company, all_child_group_ids, account_account_type_obj)
                set_column = self.group_dynamic_column_list[company.id]
                amount = amount[0][0] if amount else 0.00
                if main_grp == self.env.ref('sbk_group.account_group_main_7') and amount != 0.0:
                    amount *= -1
                worksheet.write(self.group_row, set_column, formatLang(self.env, amount), amount_data_format)
                child_group_total += amount

            worksheet.write(self.group_row, column, formatLang(self.env, child_group_total), amount_data_format)
            self.group_row += 1
            self.recursive_account_wise_group(worksheet_data, company_ids, each, account_account_type_obj, main_grp,
                                              space)

    @api.multi
    def company_pnl_data(self, company_id, each, account_account_type_obj):
        """
            Get the Journal Item data based on given company,Account Group and Account type.
            :param company_ids: company recordset
            :param each: group recordset
            :param account_account_type_obj: account_type recordset
            :return: List of tuple contains journal item specific column
        """
        query_res = []
        account_obj = self.env['account.account'].sudo()
        account_ids = account_obj.search([('company_id', '=', company_id.id),
                                          ('group_id', '=', each.id)])
        if not account_ids:
            return []

        self._cr.execute("""
        SELECT
            aml.account_id as account_id,
            sum(aml.balance) AS Total
            FROM
            account_move_line aml
            LEFT JOIN account_move move on 
            move.id=aml.move_id
            WHERE aml.company_id = %s
            AND aml.user_type_id in %s
            AND aml.account_id in %s
            AND aml.date >= %s
            AND aml.date <= %s
            AND aml.my_acc_group_id is not null
            AND move.state = 'posted'
            GROUP BY
            aml.account_id,
            aml.company_id
        """, (
        company_id.id, tuple(account_account_type_obj.ids), tuple(account_ids.ids), self.start_date, self.end_date))
        query_res = self._cr.fetchall()
        return query_res

    @api.multi
    def group_wise_pnl_data(self, company_id, each, account_account_type_obj):
        """
            Get the Journal Item data based on given company,Account Group and Account type.
            :param company_id: company recordset
            :param each: group recordset
            :param account_account_type_obj: account_type recordset
            :return: List of tuple contains journal item specific column
        """
        amount = 0.00
        self._cr.execute("""
        SELECT
            COALESCE(sum(aml.balance),0) AS Total
            FROM
            account_move_line aml
            LEFT JOIN account_move move on 
            move.id=aml.move_id
            WHERE aml.company_id = %s
            AND aml.user_type_id in %s
            AND aml.date >= %s
            AND aml.date <= %s
            AND aml.my_acc_group_id is not null
            AND aml.my_acc_group_id in %s
            AND move.state = 'posted'

        """, (company_id.id, tuple(account_account_type_obj.ids), self.start_date, self.end_date, tuple(each.ids)))
        amount = self._cr.fetchall()
        return amount

    def account_grp_wise_xls_report(self, workbook):
        """
            Create a new sheet into single workbook and print the
            account main group->Sub Group Total.
        """
        self.group_dynamic_column_list = {}
        self.group_grand_total_dict = {}
        self.group_company_dynamic_column_list = {}
        worksheet = workbook.add_worksheet('Group Report')

        bank_balance_merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'underline': 1, 'valign': 'vcenter', \
             'font_size': 32})
        bank_balance_report_merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', \
                                                                'font_size': 8, 'bg_color': '#808080'})

        statement_merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 10, \
             'num_format': 'dd/mm/yy'})

        header_merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', \
                                                   'font_size': 10, 'border': 1})

        amount_data_format = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 9})

        main_group_data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'font_size': 9, 'bold': True})
        group_total_data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'font_size': 9, 'bold': True, 'bg_color': '#808080'})
        amount_group_total_data_format = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'font_size': 9, 'bold': True, 'bg_color': '#808080'})

        module_path = get_module_path('bista_account_report')
        module_path += '/static/image/sbk_image.jpg'

        worksheet.insert_image(0, 0, module_path)

        if self.company_ids:
            company_ids = self.company_ids
        else:
            company_ids = self.env['res.company'].sudo().search([])

        name = "OFFICE AND PALACE OF HH DR.SHEIKH SULTAN BIN KHALIFA BIN ZAYED AL NAHYAN" + "\n" \
               + "CONSOLIDATED PROFIT LOSS AS ON " + datetime.strptime(self.end_date, '%Y-%m-%d').strftime("%d-%B-%y")

        merge_end_no = len(company_ids.ids) + 1
        worksheet.merge_range(0, 0, 5, 2, "", bank_balance_merge_format)
        worksheet.merge_range(8, 0, 9, merge_end_no, name, bank_balance_report_merge_format)
        worksheet.merge_range(4, 3, 4, 4, "All Amount in AED", statement_merge_format)
        worksheet.set_column(0, len(company_ids), 20)
        worksheet.write(12, 0, 'Details', header_merge_format)
        row = 12
        column = 1
        group_pnl_data = {}
        for company in company_ids:
            worksheet.write(row, column, company.name, header_merge_format)
            self.group_grand_total_dict.setdefault(column, 0.00)
            self.group_company_dynamic_column_list.setdefault(company.id, 0.00)
            self.group_dynamic_column_list.setdefault(company.id, column)
            group_pnl_data.setdefault(company.id, [])
            column += 1

        worksheet.write(row, column, "Total", header_merge_format)
        account_account_type_obj = self.common_account_type()
        account_grp_obj = self.common_account_group_obj(company_ids, account_account_type_obj)

        worksheet.set_column(1, column, 20)

        for main_grp in account_grp_obj:
            main_group_total = 0.00
            worksheet.write(self.group_row, 0, main_grp.name, main_group_data_format)
            child_ids = self.env['account.group'].search([('parent_id', '=', main_grp.id)])
            self.group_row += 1
            for child_group in child_ids:
                all_child_group_ids = self.env['account.group'].search([('parent_id', 'child_of', child_group.id)])
                worksheet.write(self.group_row, 0, child_group.name.rjust(len(child_group.name) + self.space),
                                main_group_data_format)
                sub_group_total = 0.00
                for company in company_ids:
                    amount = self.group_wise_pnl_data(company, all_child_group_ids, account_account_type_obj)
                    set_column = self.group_dynamic_column_list[company.id]
                    amount = amount[0][0] if amount else 0.00
                    if main_grp == self.env.ref('sbk_group.account_group_main_7') and amount != 0.0:
                        amount *= -1
                    worksheet.write(self.group_row, set_column, formatLang(self.env, amount), amount_data_format)
                    sub_group_total += amount

                worksheet.write(self.group_row, column, formatLang(self.env, sub_group_total), amount_data_format)

                self.group_row += 1
                worksheet_data = {'worksheet': worksheet, 'row': self.group_row, 'column': column,
                                  'format': main_group_data_format, 'workbook': workbook}
                self.recursive_account_wise_group(worksheet_data, company_ids, child_group, account_account_type_obj,
                                                  main_grp, self.space)
            self.group_row += 1

            worksheet.write(self.group_row, 0, "Total  " + main_grp.name, group_total_data_format)

            all_child_group_ids = self.env['account.group'].search([('parent_id', 'child_of', main_grp.id)])

            for company in company_ids:
                amount = self.group_wise_pnl_data(company, all_child_group_ids, account_account_type_obj)
                set_column = self.group_dynamic_column_list[company.id]
                amount = amount[0][0] if amount else 0.00
                if main_grp == self.env.ref('sbk_group.account_group_main_7') and amount != 0.0:
                    amount *= -1
                group_pnl_data[company.id].append(abs(amount))
                worksheet.write(self.group_row, set_column, formatLang(self.env, abs(amount)),
                                amount_group_total_data_format)
                main_group_total += amount

            worksheet.write(self.group_row, column, formatLang(self.env, main_group_total),
                            amount_group_total_data_format)
            self.group_row += 2
        total_profit_loss = 0.0
        for company in company_ids:
            set_column = self.group_dynamic_column_list[company.id]
            profit_loss = group_pnl_data[company.id][0] - group_pnl_data[company.id][1]
            total_profit_loss += profit_loss
            worksheet.write(self.group_row, 0, 'Profit/Loss', group_total_data_format)
            worksheet.write(self.group_row, set_column, formatLang(self.env, profit_loss),
                            amount_group_total_data_format)
        total_column = len(group_pnl_data) + 1
        worksheet.write(self.group_row, total_column, formatLang(self.env, total_profit_loss),
                        amount_group_total_data_format)

    def common_account_type(self):
        """
            Common Method to find the the Account Type.
        """
        account_account_type_obj = self.env['account.account.type'].sudo()

        # Income Account Types
        account_account_type_obj |= self.env.ref('account.data_account_type_other_income')
        account_account_type_obj |= self.env.ref('account.data_account_type_revenue')
        # Expense Account Types
        account_account_type_obj |= self.env.ref('account.data_account_type_direct_costs')
        account_account_type_obj |= self.env.ref('account.data_account_type_expenses')
        account_account_type_obj |= self.env.ref('account.data_account_type_depreciation')

        return account_account_type_obj

    def common_account_group_obj(self, company_ids, account_account_type_obj):
        """
            Common Method to find the the Account Group and used that group in 
            Journal Item for perticular date.
        """
        account_grp_obj = self.env['account.group']
        self._cr.execute("""
                            SELECT DISTINCT(aml.my_acc_group_id) as acc_grp_id
                            FROM
                            account_move_line aml
                            WHERE aml.company_id in %s
                            AND aml.user_type_id in %s
                            AND aml.date >= %s
                            AND aml.date <= %s
                            AND aml.my_acc_group_id is not null
        """, (tuple(company_ids.ids), tuple(account_account_type_obj.ids), self.start_date, self.end_date))
        query_res = self._cr.fetchall()
        final_grp_lst = []
        for each_res in query_res:
            final_grp_lst.extend(list(each_res))

        for each_grp in self.env['account.group'].browse(final_grp_lst):
            account_grp_obj |= self.find_parent_group(each_grp)

        return account_grp_obj.sorted(key=lambda r: r.sequence)
