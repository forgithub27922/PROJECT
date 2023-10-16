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
from dateutil import parser
from datetime import datetime as dt_dt
from dateutil.relativedelta import relativedelta as rd
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import calendar


class balance_sheet_account_grp_report(models.AbstractModel):
    _name = 'report.bista_account_report.balance_sheet_account_grp_report'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id', []))

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'get_account_type_value': self.get_account_type_value,
            'query_execute': self.query_execute,
            'get_total_of_group': self.get_total_of_group,
            'get_unallocated_earning': self.get_unallocated_earning,
            'get_group_child_level':self.get_group_child_level
        }

    def get_child_ids(self, group_id, child_ids=[]):
        childs = self.env['account.group'].search([('parent_id', '=', group_id.id)])
        for child in childs:
            child_ids += [child.id]
            self.get_child_ids(child, child_ids)
        return child_ids

    def get_group_child_level(self, group_id, record):
        """
            Method to use for if group have all child not show in report
            then remove the extra line from q-web and amout will shown in single row with group name.
            for Ex: Land have child group and if all child will not displayed
                in report then we remove the Total of line and amount will shown with single line of group.
        """
        group_child_ids = self.env['account.group'].search([('parent_id', 'child_of', group_id.id),('id','!=',group_id.id)])
        flag = False
        if any(group_child_ids.filtered(lambda l:l.display_in_bs_report)):
            flag = True
        else:
            flag = False
        return flag

    def get_total_of_group(self, group_id, record, flag=False):
        childs = self.get_child_ids(group_id, child_ids=[])
        childs = list(set(childs))
        qry_data = self.query_execute(group_id, record, flag)
        total_pyytd = total_cyytd = 0.0

        if len(childs) > 1:
            child_pyytd_total = child_cyytd_total = 0
            for child in childs:
                child_qry = self.query_execute(child, record, flag=flag)
                if child_qry:
                    if isinstance(child_qry, list):
                        for child_qr in child_qry:
                            child_cyytd_total += child_qr and child_qr[0] or 0.0
                            child_pyytd_total += child_qr and child_qr[1] or 0.0

                    else:
                        child_cyytd_total += child_qry and child_qry[0] or 0.0
                        child_pyytd_total += child_qry and child_qry[1] or 0.0

            if isinstance(qry_data, list):
                for child_qr in qry_data:
                    total_cyytd += child_qr and child_qr[0] or 0.0
                    total_pyytd += child_qr and child_qr[1] or 0.0
                
            else:
                total_cyytd = (qry_data and qry_data[0] or 0.0) + child_cyytd_total
                total_pyytd = (qry_data and qry_data[1] or 0.0) + child_pyytd_total

            if abs(total_cyytd) > 0.0 or abs(total_pyytd) > 0.0:
                return total_cyytd, total_pyytd, True if abs(child_cyytd_total) > 0.0 or abs(child_pyytd_total) > 0.0 else False
            else:
                return total_cyytd, total_pyytd, False
        else:
            if isinstance(qry_data, list):
                for qry in qry_data:
                    total_cyytd += qry and qry[0] or 0.0
                    total_pyytd += qry and qry[1] or 0.0
            else:
                total_pyytd = qry_data and qry_data[1] or 0.0
                total_cyytd = qry_data and qry_data[0] or 0.0

            return total_cyytd, total_pyytd, False

    def query_execute(self, l, record, flag=False):
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        target_move = ''
        new_target_move = ''
        if record.target_move != 'all':
            target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
            new_target_move = "AND m.state = 'posted' "

        account_account_type_obj = self.env['account.account.type']
        if not isinstance(l, int):
            l = l.id

        # Assets
        account_account_type_obj |= self.env.ref('account.data_account_type_non_current_assets')
        account_account_type_obj |= self.env.ref('account.data_account_type_fixed_assets')
        account_account_type_obj |= self.env.ref('account.data_account_type_prepayments')
        account_account_type_obj |= self.env.ref('account.data_account_type_current_assets')
        account_account_type_obj |= self.env['account.account.type'].search([('type', '=', 'receivable')])
        account_account_type_obj |= self.env.ref('account.data_account_type_liquidity')

        # Liabilities
        account_account_type_obj |= self.env.ref('account.data_account_type_non_current_liabilities')
        account_account_type_obj |= self.env['account.account.type'].search([('type', '=', 'payable')])
        account_account_type_obj |= self.env.ref('account.data_account_type_current_liabilities')
        account_account_type_obj |= self.env.ref('account.data_account_type_credit_card')

        # Equity
        # account_account_type_obj |= self.env.ref('account.data_account_type_equity')
        account_account_type_obj |= self.env.ref('account.data_unaffected_earnings')
        account_account_type_obj |= self.env.ref('account.data_account_type_other_income')
        account_account_type_obj |= self.env.ref('account.data_account_type_revenue')
        account_account_type_obj |= self.env.ref('account.data_account_type_direct_costs')
        account_account_type_obj |= self.env.ref('account.data_account_type_expenses')
        account_account_type_obj |= self.env.ref('account.data_account_type_depreciation')

        account_type_ids = tuple([x.id for x in account_account_type_obj])

        fixed_asset_grp = self.env.ref('sbk_group.account_group_main_1')
        curr_ass_loan = self.env.ref('sbk_group.account_group_main_3')
        investment_grp = self.env.ref('sbk_group.account_group_main_2')

        childs = self.get_child_ids(fixed_asset_grp, child_ids=[])
        childs += self.get_child_ids(curr_ass_loan, child_ids=[])
        childs += self.get_child_ids(investment_grp, child_ids=[])
        childs += [fixed_asset_grp.id, curr_ass_loan.id, investment_grp.id]
        sign = '-'
        if l in childs:
            sign = "+"

        if flag:
            account_ids = self.env['account.account'].search([('company_id', '=', record.company_id.id),
                                                              ('group_id', '=', l)])
            if account_ids:
                if len(account_ids) == 1:
                    z = "(" + str(account_ids[0].id) + ")"
                else:
                    z = tuple(account_ids.mapped('id'))
                self._cr.execute("""
                    SELECT
                                            aml.my_acc_group_id as my_acc_group_id,
                                            aml.account_id as account_id,
                                            sum(aml.current_year_ytd) AS CYYTD,
                                            sum(aml.previous_year_ytd) AS PYYTD
                                        from (
                                            SELECT
                                                my_acc_group_id,account_id,
                                                case
                                                    when (ml.date <= '%s')
                                                    THEN %ssum(balance)
                                                    ELSE
                                                    0.00
                                                    end as current_year_ytd,

                                                case
                                                    when (ml.date <= '%s')
                                                    THEN %ssum(balance)
                                                    ELSE
                                                    0.00
                                                end as previous_year_ytd

                                            FROM
                                                account_move_line as ml 
                                                %s
                                                WHERE ml.company_id = %s
                                                AND my_acc_group_id = %s
                                                AND account_id in %s
                                                AND user_type_id in %s
                                                %s

                                            GROUP BY 
                                                my_acc_group_id,ml.date,account_id
                                            ) as aml

                                        GROUP BY

                                        my_acc_group_id,account_id
                                """ % (date, sign or '+', py_date, sign or '+', target_move, record.company_id.id, l, z, account_type_ids, new_target_move))

            query_res_data = self._cr.fetchall()
            if query_res_data:
                list = []
                for query_res in query_res_data:

                    account = query_res and query_res[1] or False
                    cyytd = query_res and query_res[2] or 0.0
                    pyytd = query_res and query_res[3] or 0.0
                    if abs(cyytd) > 0.0 or abs(pyytd) > 0.0:
                        list.append([cyytd, pyytd, account])

                return list
            else:
                return None
        else:

            self._cr.execute(""" SELECT sum(aml.current_year_ytd) AS CYYTD, sum(aml.previous_year_ytd) AS PYYTD
                        from (SELECT my_acc_group_id,
                                case
                                    when (ml.date <= '%s')
                                        THEN %ssum(balance)
                                    ELSE
                                    0.00
                                    end as current_year_ytd,

                                case
                                    when (ml.date <= '%s')
                                    THEN %ssum(balance)
                                    ELSE
                                    0.00
                                end as previous_year_ytd

                            FROM
                                account_move_line as ml
                                %s
                                WHERE ml.company_id = %s
                                AND my_acc_group_id = %s
                                AND user_type_id in %s
                                %s
                                
                            GROUP BY  my_acc_group_id,ml.date ) as aml
                        GROUP BY my_acc_group_id  """ % (date, sign or '+', py_date, sign or '+', target_move, record.company_id.id, l, account_type_ids, new_target_move))
            query_res = self._cr.fetchone()
            cyytd = query_res and query_res[0] or 0.0
            pyytd = query_res and query_res[1] or 0.0

            if not (abs(cyytd) > 0.0 or abs(pyytd) > 0.0):
                return None

        return cyytd, pyytd

    def get_unallocated_earning(self, record):
        account_obj = self.env['account.account.type']
        account_obj1 = account_obj + self.env.ref('account.data_account_type_revenue')
        account_obj1 += self.env.ref('account.data_account_type_other_income')
        account_obj2 = account_obj + self.env.ref('account.data_account_type_direct_costs')
        account_obj2 += self.env.ref('account.data_account_type_expenses')
        account_obj2 += self.env.ref('account.data_account_type_depreciation')
        account_obj3 = self.env.ref('account.data_account_type_equity')

        # Retained Earnings CY (C.Y. YTD)
        cy_start_date = record.date.split('-')[0] + '-' + '01-01'
        # cy_end_date = record.date.split('-')[0] + '-' + '12-31'
        if record.target_move == 'posted':
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', record.date),
                 ('date', '>=', cy_start_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', record.date),
                 ('date', '>=', cy_start_date),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
        else:
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', record.date),
                 ('date', '>=', cy_start_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', record.date),
                 ('date', '>=', cy_start_date),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('company_id', '=', record.company_id.id)])

        sum_of_inc = sum_of_exp = 0.0
        for inc in INCOME:
            sum_of_inc += inc.balance
        for exp in EXPENSE:
            sum_of_exp += exp.balance
        re_cy_cyytd = sum_of_inc + sum_of_exp
        re_cy_cyytd *= -1

        # Retained Earnings CY (P.Y. YTD)
        # py_date = str((parser.parse(record.date) - rd(years=1)).date())
        strp_dt = dt_dt.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        py_start_date = py_date.split('-')[0] + '-' + '01-01'
        py_end_date = py_date.split('-')[0] + '-' + '12-31'
        if record.target_move == 'posted':
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_date),
                 ('date', '>=', py_start_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_date),
                 ('date', '>=', py_start_date),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
        else:
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_date),
                 ('date', '>=', py_start_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_date),
                 ('date', '>=', py_start_date),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('company_id', '=', record.company_id.id)])

        sum_of_inc = sum_of_exp = 0.0
        for inc in INCOME:
            sum_of_inc += inc.balance
        for exp in EXPENSE:
            sum_of_exp += exp.balance
        re_cy_pyytd = sum_of_inc + sum_of_exp
        re_cy_pyytd *= -1

        #Retained Earnings PY (C.Y. YTD)
        # PNL Of ALL PREVIOUS YEARS BEFORE CURRENT YEAR
        if record.target_move == 'posted':
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_end_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_end_date),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
        else:
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_end_date),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_end_date)
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('company_id', '=', record.company_id.id)])
        sum_of_inc = sum_of_exp = 0.0
        for inc in INCOME:
            sum_of_inc += inc.balance
        for exp in EXPENSE:
            sum_of_exp += exp.balance
        pnl_pyytd = sum_of_inc + sum_of_exp

        # Retained Earnings / Equity up to current date
        EQUITY = self.env['account.move.line'].search(
            [('date', '<=', record.date),
             ('account_id.user_type_id', 'in', account_obj3.ids),
             ('company_id', '=', record.company_id.id)])
        sum_of_py_eqt = 0.0
        for eqt in EQUITY:
            sum_of_py_eqt += eqt.balance
        re_py_cyytd = pnl_pyytd + sum_of_py_eqt
        re_py_cyytd *= -1

        # PNL Of ALL PREVIOUS YEARS BEFORE PREVIOUS YEAR
        py_date2 = str((parser.parse(py_date) - rd(years=1)).date())
        # py_start_date2 = py_date2.split('-')[0] + '-' + '01-01'
        py_end_date2 = py_date2.split('-')[0] + '-' + '12-31'
        if record.target_move == 'posted':
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_end_date2),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_end_date2),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('move_id.state', '=', 'posted'),
                 ('company_id', '=', record.company_id.id)])
        else:
            INCOME = self.env['account.move.line'].search(
                [('date', '<=', py_end_date2),
                 ('account_id.user_type_id', 'in', account_obj1.ids),
                 ('company_id', '=', record.company_id.id)])
            EXPENSE = self.env['account.move.line'].search(
                [('date', '<=', py_end_date2),
                 ('account_id.user_type_id', 'in', account_obj2.ids),
                 ('company_id', '=', record.company_id.id)])

        sum_of_inc = sum_of_exp = 0.0
        for inc in INCOME:
            sum_of_inc += inc.balance
        for exp in EXPENSE:
            sum_of_exp += exp.balance
        pnl_pyytd2 = sum_of_inc + sum_of_exp
        # Retained Earnings / Equity up to current date previous year
        EQUITY = self.env['account.move.line'].search(
            [('date', '<=', py_date),
             ('account_id.user_type_id', 'in', account_obj3.ids),
             ('company_id', '=', record.company_id.id)])
        sum_of_py_eqt2 = 0.0
        for eqt in EQUITY:
            sum_of_py_eqt2 += eqt.balance
        re_py_pyytd = pnl_pyytd2 + sum_of_py_eqt2
        re_py_pyytd *= -1

        liab_grp = self.env['account.group'].search([('name', '=', 'Liabilities')])
        laib_total = self.get_total_of_group(liab_grp, record)
        cyytd_laib_total = laib_total and laib_total[0] or 0.0
        pyytd_laib_total = laib_total[1] and laib_total[1] or 0.0

        cyytd_total_liablity = re_py_cyytd + re_cy_cyytd + cyytd_laib_total
        pyytd_total_liablity = re_py_pyytd + re_cy_pyytd + pyytd_laib_total

        return re_cy_cyytd or 0.0, re_py_cyytd or 0.0, re_cy_pyytd or 0.0,\
               re_py_pyytd or 0.0, cyytd_total_liablity or 0.0, \
               pyytd_total_liablity or 0.0

    def get_account_type_value(self, record):
        acc_group_ids = record.acc_group_ids
        if not acc_group_ids:

            # fixed_asset_grp = self.env.ref('sbk_group.account_group_main_1')
            # curr_ass_loan = self.env.ref('sbk_group.account_group_main_3')
            # current_laib_grp = self.env.ref('sbk_group.account_group_main_5')
            # equity_grp = self.env.ref('sbk_group.account_group_main_6')
            asset = self.env['account.group'].search([('name', '=', 'Assets')])
            liab_grp = self.env['account.group'].search([('name', '=', 'Liabilities')])

            account_grp_obj = asset + liab_grp

            return self.env['account.group'].search([('id', 'in', account_grp_obj.ids)], order='id asc'), True
        else:
            return acc_group_ids, False
