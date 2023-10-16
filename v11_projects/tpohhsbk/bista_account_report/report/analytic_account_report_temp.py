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
from datetime import datetime as dt_dt
from dateutil.relativedelta import relativedelta as rd
import calendar
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

global acc_grp_total_rec
acc_grp_total_rec = []

global analytic_acc_total_grp
analytic_acc_total_grp = []

global analytic_grp_total_grp
analytic_grp_total_grp = []


class bista_account_report_analytic(models.AbstractModel):
    _name = 'report.bista_account_report.bista_analytic_account_report_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))

        date = data.get('date')

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'get_income_account_value':self.get_income_account_value,
            'get_exp_analytic_account_value':self.get_exp_analytic_account_value,
            'group_wise_analytic_account_value':self.group_wise_analytic_account_value,
            'analytic_grp_acc_wise_report_vals':self.analytic_grp_acc_wise_report_vals,
            'analytic_acc_wise_report_data':self.analytic_acc_wise_report_data,
            'total_income_value':self.total_income_value,
            'analytic_grp_acc_wise_total':self.analytic_grp_acc_wise_total
        }

    def total_income_value(self, record):
        income_group_lst = []
        account_type_id = self.env.ref('account.data_account_type_revenue') \
                        +self.env.ref('account.data_account_type_other_income')\
                        +self.env.ref('account.data_account_type_direct_costs')

        account_grp_obj = self.env['account.group']
        self._cr.execute("""
                            SELECT aml.my_acc_group_id as acc_grp_id
                            FROM
                            account_move_line aml
                            where aml.user_type_id in %s 
                            AND aml.company_id = %s
                            GROUP BY
                            aml.my_acc_group_id
        """ % (tuple(account_type_id.ids), record.company_id.id))
        query_res = self._cr.fetchall()
        final_grp = []
        for x in query_res:
            final_grp.extend(list(x))
        for each_grp in self.env['account.group'].browse(final_grp):
            account_grp_obj |= self.find_parent(each_grp)

        main_grp_lst = [x.id for x in account_grp_obj]
        income_group_lst = final_grp + main_grp_lst
        if income_group_lst:
            return self.get_income_grp_total_value(record, income_group_lst, income=True)
        else:
            return False

    # 1st page Report
    def get_income_account_value(self, record):
        account_type_id = self.env.ref('account.data_account_type_revenue') \
                        +self.env.ref('account.data_account_type_other_income')\
                        +self.env.ref('account.data_account_type_direct_costs')

        account_grp_obj = self.env['account.group']
        self._cr.execute("""
                            SELECT aml.my_acc_group_id as acc_grp_id
                            FROM
                            account_move_line aml
                            where aml.user_type_id in %s 
                            AND aml.company_id = %s
                            GROUP BY
                            aml.my_acc_group_id
        """ % (tuple(account_type_id.ids), record.company_id.id))
        query_res = self._cr.fetchall()
        final_grp = []
        for x in query_res:
            final_grp.extend(list(x))
        for each_grp in self.env['account.group'].browse(final_grp):
            account_grp_obj |= self.find_parent(each_grp)

        for main_grp in account_grp_obj:
            acc_grp_total_rec.append(main_grp.id)
            # Main Group
            tbody_template = """
                    <tr style="font-weight:bold;border-bottom:2px solid;">
                        <td colspan="5">%s</td>
                    </tr>
            """ % (main_grp.name)
            child_ids = self.env['account.group'].search([('parent_id', '=', main_grp.id)])
            for each in child_ids:
                qry_res = self.get_account_type_value(record, each)
                grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
                if qry_res:
                    acc_grp_total_rec.append(each.id)
                    # Sub Group
                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:1px solid;">
                            <td style=%s colspan="5"> %s </td>
                        </tr>
                    """ % (style, each.name)

                    style = "padding-left:40px;"
                    for qry in qry_res:
                         cy_mtd = formatLang(self.env, qry[1])
                         py_mtd = formatLang(self.env, qry[2])
                         cy_ytd = formatLang(self.env, qry[3])
                         py_ytd = formatLang(self.env, qry[4])
                         account_id = self.env['account.account'].sudo().browse(qry[0])
                         tbody_template += """
                                                <tr style="font-weight:bold;border-bottom:1px solid;">
                                                    <td style=%s> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                </tr>
                                            """ % (style, account_id.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)
                         grp_cy_mtd += qry[1]
                         grp_py_mtd += qry[2]
                         grp_cy_ytd += qry[3]
                         grp_py_ytd += qry[4]

                    tbody_template = self.recursive_group(record, each, tbody_template, level=2)

                    #  Sub Group Total

                    grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                    grp_py_mtd = formatLang(self.env, grp_py_mtd)
                    grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                    grp_py_ytd = formatLang(self.env, grp_py_ytd)

                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                            <td style=%s>Total %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                        </tr>
                    """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)

            grp_unique_list = list(set(acc_grp_total_rec))
            grp_unique_list = list(filter(lambda ele: ele, grp_unique_list))
            qry_res = self.get_income_grp_total_value(record, grp_unique_list, income=True)

            total_cy_mtd = formatLang(self.env, qry_res[0])
            total_py_mtd = formatLang(self.env, qry_res[1])
            total_cy_ytd = formatLang(self.env, qry_res[2])
            total_py_ytd = formatLang(self.env, qry_res[3])

            tbody_template += """
                <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                    <td>Total %s </td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                </tr>
            """ % (main_grp.name, total_cy_mtd, total_py_mtd, total_cy_ytd, total_py_ytd)
            return tbody_template

    def recursive_group(self, record, grp, template, level):
        acc_grp_total_rec.append(grp.id)
        child_ids = self.env['account.group'].search([('parent_id', '=', grp.id)])
        if level == 2:
            style = "padding-left:40px;"
        elif level > 2:
            style = "padding-left:60px;"
        else:
            style = "padding-left:None;"
        # Recursion Group Function
        for each in child_ids:
            qry_res = self.get_account_type_value(record, each)
            grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
            if qry_res:
                acc_grp_total_rec.append(each.id)
                template += """ 
                    <tr style="font-weight:bold;border-bottom:1px solid;">
                        <td style=%s colspan="5">%s</td>
                    </tr>
                """ % (style, each.name)

                style = "padding-left:60px;"
                for qry in qry_res:

                    cy_mtd = formatLang(self.env, qry[1])
                    py_mtd = formatLang(self.env, qry[2])
                    cy_ytd = formatLang(self.env, qry[3])
                    py_ytd = formatLang(self.env, qry[4])

                    account_id = self.env['account.account'].sudo().browse(qry[0])
                    template += """
                                        <tr style="font-weight:bold;border-bottom:1px solid;">
                                            <td style=%s> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                        </tr>
                                    """ % (style, account_id.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)

                    grp_cy_mtd += qry[1]
                    grp_py_mtd += qry[2]
                    grp_cy_ytd += qry[3]
                    grp_py_ytd += qry[4]

#                 Sub Group Total
                grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                grp_py_mtd = formatLang(self.env, grp_py_mtd)
                grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                grp_py_ytd = formatLang(self.env, grp_py_ytd)

                style = "padding-left:40px;"
                template += """
                    <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                        <td style=%s>Total %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                    </tr>
                """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)
                template = self.recursive_group(record, each, template, level)
                level += 1
        return template

    # 3rd Page report values
    def analytic_grp_acc_wise_report_vals(self, record, analytic_grp):
        account_grp_obj = self.env['account.group']
        account_type_id = self.env.ref('account.data_account_type_expenses')
        self._cr.execute("""
                            SELECT aml.my_acc_group_id as acc_grp_id
                            FROM
                            account_move_line aml
                            where aml.user_type_id = %s 
                            AND aml.company_id = %s
                            AND aml.analytic_acc_group_id = %s
                            GROUP BY 
                            aml.my_acc_group_id
        """ % (account_type_id.id, record.company_id.id, analytic_grp.id))
        query_res = self._cr.fetchall()
        final_grp = []
        for x in query_res:
            final_grp.extend(list(x))
        for each_grp in self.env['account.group'].browse(final_grp):
            account_grp_obj |= self.find_parent(each_grp)

        tbody_template = ""
        for main_grp in account_grp_obj:
            analytic_grp_total_grp = []
            analytic_grp_total_grp.append(main_grp.id)
#             acc_grp_total_rec.append(main_grp.id)
            # Main Group
            tbody_template += """
                    <tr style="font-weight:bold;border-bottom:2px solid;">
                        <td colspan="5">%s</td>
                    </tr>
            """ % (main_grp.name)
#             child_ids = self.env['account.group'].search([('parent_id', '=', main_grp.id)])
            child_ids = analytic_grp.account_group_ids
            for each in child_ids:
                qry_res = self.analytic_grp_acc_wise_report(record, each, analytic_grp)
#                 grp_wise_total_amt = self.analytic_grp_acc_wise_total(record, each, analytic_grp)
                grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
                if qry_res:
                    analytic_grp_total_grp.append(each.id)

#                     grp_total_cy_mtd = formatLang(self.env, grp_wise_total_amt[0][0])
#                     grp_total_py_mtd = formatLang(self.env, grp_wise_total_amt[0][1])
#                     grp_total_cy_ytd = formatLang(self.env, grp_wise_total_amt[0][2])
#                     grp_total_py_ytd = formatLang(self.env, grp_wise_total_amt[0][3])

                    # Sub Group
                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                            <td colspan="5" style=%s> %s </td>
                        </tr>
                    """ % (style, each.name)

#                         <td class="text-right"> %s </td>
#                             <td class="text-right"> %s </td>
#                             <td class="text-right"> %s </td>
#                             <td class="text-right"> %s </td>

                    style = "padding-left:40px;"
                    for key , value in sorted(qry_res.items(),key=lambda key: key[0].code):
                        cy_mtd = formatLang(self.env, value[0])
                        py_mtd = formatLang(self.env, value[1])
                        cy_ytd = formatLang(self.env, value[2])
                        py_ytd = formatLang(self.env, value[3])
#                         account_id = self.env['account.account'].sudo().browse(qry[0])
                        tbody_template += """
                                                <tr style="font-weight:bold;border-bottom:1px solid;">
                                                    <td style=%s> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                </tr>
                                            """ % (style, key.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)
                        grp_cy_mtd += value[0]
                        grp_py_mtd += value[1]
                        grp_cy_ytd += value[2]
                        grp_py_ytd += value[3]

#                     tbody_template = self.recursive_group_analytic_grp(record, each, tbody_template, analytic_grp, level=2)

                    #  Sub Group Total
                    grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                    grp_py_mtd = formatLang(self.env, grp_py_mtd)
                    grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                    grp_py_ytd = formatLang(self.env, grp_py_ytd)

                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                            <td style=%s>Total %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                        </tr>
                    """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)

            grp_unique_list = list(set(analytic_grp_total_grp))
            qry_res = self.with_context({'analytic_grp':analytic_grp}).get_income_grp_total_value(record, grp_unique_list, income=False)
            total_cy_mtd = formatLang(self.env, qry_res[0])
            total_py_mtd = formatLang(self.env, qry_res[1])
            total_cy_ytd = formatLang(self.env, qry_res[2])
            total_py_ytd = formatLang(self.env, qry_res[3])
            tbody_template += """
                <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                    <td>Total %s </td>

                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                </tr>
            """ % (main_grp.name, total_cy_mtd, total_py_mtd, total_cy_ytd, total_py_ytd)
        return tbody_template

    def recursive_group_analytic_grp(self, record, each, template, analytic_grp, level):
        analytic_grp_total_grp.append(each.id)
        child_ids = self.env['account.group'].search([('parent_id', '=', each.id)])
        if level == 2:
            style = "padding-left:40px;"
        elif level > 2:
            style = "padding-left:60px;"
        else:
            style = "padding-left:None;"
        # Recursion Group Function
        for each in child_ids:
            qry_res = self.analytic_grp_acc_wise_report(record, each, analytic_grp)
            grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
            if qry_res:
                analytic_grp_total_grp.append(each.id)
                template += """ 
                    <tr style="font-weight:bold;border-bottom:1px solid;">
                        <td style=%s colspan="5">%s</td>
                    </tr>
                """ % (style, each.name)

                style = "padding-left:60px;"
                for qry in qry_res:
                    cy_mtd = formatLang(self.env, qry[1])
                    py_mtd = formatLang(self.env, qry[2])
                    cy_ytd = formatLang(self.env, qry[3])
                    py_ytd = formatLang(self.env, qry[4])
                    account_id = self.env['account.account'].sudo().browse(qry[0])
                    template += """
                                        <tr style="font-weight:bold;border-bottom:1px solid;">
                                            <td style=%s> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                        </tr>
                                    """ % (style, account_id.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)

                    grp_cy_mtd += qry[1]
                    grp_py_mtd += qry[2]
                    grp_cy_ytd += qry[3]
                    grp_py_ytd += qry[4]

#                 Sub Group Total
                grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                grp_py_mtd = formatLang(self.env, grp_py_mtd)
                grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                grp_py_ytd = formatLang(self.env, grp_py_ytd)

                style = "padding-left:40px;"
                template += """
                    <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                        <td style=%s>Total %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                    </tr>
                """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)
                template = self.recursive_group_analytic_grp(record, each, template, analytic_grp, level)
                level += 1
        return template

    # 4th Report
    def analytic_acc_wise_report_data(self, record, analytic_acc):
        account_grp_obj = self.env['account.group']
        account_type_id = self.env.ref('account.data_account_type_expenses')
        self._cr.execute("""
                            SELECT aml.my_acc_group_id as acc_grp_id
                            FROM
                            account_move_line aml
                            where aml.user_type_id = %s 
                            AND aml.company_id = %s
                            AND aml.analytic_account_id = %s
                            GROUP BY 
                            aml.my_acc_group_id
        """ % (account_type_id.id, record.company_id.id, analytic_acc.id))
        query_res = self._cr.fetchall()
        final_grp = []
        for x in query_res:
            final_grp.extend(list(x))
        for each_grp in self.env['account.group'].browse(final_grp):
            account_grp_obj |= self.find_parent(each_grp)

        tbody_template = ""
        for main_grp in account_grp_obj:
            analytic_acc_total_grp.append(main_grp.id)
            # Main Group
            tbody_template += """
                    <tr style="font-weight:bold;border-bottom:2px solid;">
                        <td colspan="5">%s</td>
                    </tr>
            """ % (main_grp.name)

#             if analytic_acc.analytic_group_id and analytic_acc.analytic_group_id.account_group_ids:
            child_ids = analytic_acc.analytic_group_id.account_group_ids
#             else:
#                 child_ids = self.env['account.group'].search([('parent_id', '=', main_grp.id)])
            for each in child_ids:
                qry_res = self.analytic_acc_wise_report(record, each, analytic_acc)
                grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
                if qry_res:
                    analytic_acc_total_grp.append(each.id)
                    # Sub Group
                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:1px solid;">
                            <td style=%s colspan="5"> %s </td>
                        </tr>
                    """ % (style, each.name)
                    style = "padding-left:40px;"
                    for key , value in sorted(qry_res.items(),key=lambda key: key[0].code):
                        cy_mtd = formatLang(self.env, value[0])
                        py_mtd = formatLang(self.env, value[1])
                        cy_ytd = formatLang(self.env, value[2])
                        py_ytd = formatLang(self.env, value[3])

#                     for qry in qry_res:
#                          cy_mtd = formatLang(self.env, qry[1])
#                          py_mtd = formatLang(self.env, qry[2])
#                          cy_ytd = formatLang(self.env, qry[3])
#                          py_ytd = formatLang(self.env, qry[4])
                        tbody_template += """
                                                <tr style="font-weight:bold;border-bottom:1px solid;">
                                                    <td style=%s> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                    <td class="text-right"> %s </td>
                                                </tr>
                                            """ % (style, key.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)
                        grp_cy_mtd += value[0]
                        grp_py_mtd += value[1]
                        grp_cy_ytd += value[2]
                        grp_py_ytd += value[3]

                    if analytic_acc.analytic_group_id and not analytic_acc.analytic_group_id.account_group_ids:
                        tbody_template = self.recursive_group_analytic_acc(record, each, tbody_template, analytic_acc, level=2)

                    #  Sub Group Total
                    grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                    grp_py_mtd = formatLang(self.env, grp_py_mtd)
                    grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                    grp_py_ytd = formatLang(self.env, grp_py_ytd)

                    style = "padding-left:20px;"
                    tbody_template += """
                        <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                            <td style=%s>Total %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                            <td class="text-right"> %s </td>
                        </tr>
                    """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)

            grp_unique_list = list(set(analytic_acc_total_grp))
            qry_res = self.with_context({'analytic_acc':analytic_acc}).get_income_grp_total_value(record, grp_unique_list, income=False)
#             qry_res = self.analytic_grp_acc_wise_report(record, each, analytic_grp)
            total_cy_mtd = formatLang(self.env, qry_res[0])
            total_py_mtd = formatLang(self.env, qry_res[1])
            total_cy_ytd = formatLang(self.env, qry_res[2])
            total_py_ytd = formatLang(self.env, qry_res[3])

            tbody_template += """
                <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                    <td>Total %s </td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                    <td class="text-right">%s</td>
                </tr>
            """ % (main_grp.name, total_cy_mtd, total_py_mtd, total_cy_ytd, total_py_ytd)
        return tbody_template

    def recursive_group_analytic_acc(self, record, each, template, analytic_acc, level):
        analytic_acc_total_grp.append(each.id)
        child_ids = self.env['account.group'].search([('parent_id', '=', each.id)])
        if level == 2:
            style = "padding-left:40px;"
        elif level > 2:
            style = "padding-left:60px;"
        else:
            style = "padding-left:None;"
        # Recursion Group Function
        for each in child_ids:
            qry_res = self.analytic_acc_wise_report(record, each, analytic_acc)
            grp_cy_mtd = grp_py_mtd = grp_cy_ytd = grp_py_ytd = 0.00
            if qry_res:
                analytic_acc_total_grp.append(each.id)
                template += """ 
                    <tr style="font-weight:bold;border-bottom:1px solid;">
                        <td style=%s colspan="5">%s</td>
                    </tr>
                """ % (style, each.name)

                style = "padding-left:60px;"
                for qry in qry_res:
                    cy_mtd = formatLang(self.env, qry[1])
                    py_mtd = formatLang(self.env, qry[2])
                    cy_ytd = formatLang(self.env, qry[3])
                    py_ytd = formatLang(self.env, qry[4])
                    account_id = self.env['account.account'].sudo().browse(qry[0])
                    template += """
                                        <tr style="font-weight:bold;border-bottom:1px solid;">
                                            <td style=%s> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                            <td class="text-right"> %s </td>
                                        </tr>
                                    """ % (style, account_id.display_name, cy_mtd, py_mtd, cy_ytd, py_ytd)

                    grp_cy_mtd += qry[1]
                    grp_py_mtd += qry[2]
                    grp_cy_ytd += qry[3]
                    grp_py_ytd += qry[4]

#                 Sub Group Total
                grp_cy_mtd = formatLang(self.env, grp_cy_mtd)
                grp_py_mtd = formatLang(self.env, grp_py_mtd)
                grp_cy_ytd = formatLang(self.env, grp_cy_ytd)
                grp_py_ytd = formatLang(self.env, grp_py_ytd)

                style = "padding-left:40px;"
                template += """
                    <tr style="font-weight:bold;border-bottom:2px solid;border-top:2px solid;">
                        <td style=%s>Total %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                        <td class="text-right"> %s </td>
                    </tr>
                """ % (style, each.name, grp_cy_mtd, grp_py_mtd, grp_cy_ytd, grp_py_ytd)
                template = self.recursive_group_analytic_acc(record, each, template, analytic_acc, level)
                level += 1
        return template

    def get_income_grp_total_value(self, record, group_ids, income=None):
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if income:
            account_type_id = self.env.ref('account.data_account_type_revenue') \
                        +self.env.ref('account.data_account_type_other_income')\
                        +self.env.ref('account.data_account_type_direct_costs')

            ttype = 'credit-debit'
        else:
            account_type_id = self.env.ref('account.data_account_type_expenses')
            ttype = 'debit-credit'

        if len(account_type_id.ids) == 1:
            acc_type = "(" + str(account_type_id.id) + ")"
        else:
            acc_type = tuple(account_type_id.ids)

        if len(group_ids) == 1:
            z = "(" + str(group_ids[0]) + ")"
        else:
            z = tuple(group_ids)

        target_move = ''
        new_target_move = ''

        where_clause = "user_type_id in %s AND my_acc_group_id in %s" % (acc_type, z)

        if self._context.get('analytic_grp'):
            where_clause += " AND" + " " + "analytic_acc_group_id = %s " % self._context.get('analytic_grp').id

        if self._context.get('analytic_acc'):
            where_clause += " AND" + " " + "analytic_account_id = %s " % self._context.get('analytic_acc').id

        if record.target_move != 'all':
            target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
            new_target_move = "AND m.state = 'posted' "

        query_res = []
        self._cr.execute("""
            SELECT
                coalesce(sum(aml.current_year_mtd),0)  AS CYMTD,
                coalesce(sum(aml.previous_year_mtd),0) AS PYMTD,
                coalesce(sum(aml.current_year_ytd),0) AS CYYTD,
                coalesce(sum(aml.previous_year_ytd),0) AS PYYTD
            from (
                SELECT
                    case
                        when (ml.date >= date_trunc('month',timestamp '%s')::date)
                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                        THEN sum(%s)
                        ELSE
                        0.00
                    end as previous_year_mtd,
                    case
                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                        THEN sum(%s)
                        ELSE
                        0.00
                    end as current_year_mtd,
                    case
                        when (ml.date >= date_trunc('year',timestamp '%s')::date)
                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                        THEN sum(%s)
                        ELSE
                        0.00
                    end as current_year_ytd,
                    case
                        when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                        THEN sum(%s)
                        ELSE
                        0.00
                    end as previous_year_ytd
                FROM
                    account_move_line ml
                    %s
                    where %s
                    AND ml.company_id = %s
                    %s

                GROUP BY
                    ml.date
                ) as aml

        """ % (py_date, py_date, ttype, date, date, ttype, date, date, ttype, py_date, py_date, ttype, target_move, where_clause, record.company_id.id, new_target_move))

        query_res = self._cr.fetchone()
        return query_res

    # 1st Page Report
    def get_account_type_value(self, record, group):
        account_group_by = {}
        account_obj = self.env['account.account']
        account_group_obj = self.env['account.group']
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        account_type_id = self.env.ref('account.data_account_type_revenue') \
                        +self.env.ref('account.data_account_type_other_income')\
                        +self.env.ref('account.data_account_type_direct_costs')

        account_ids = account_obj.search([('company_id', '=', record.company_id.id),
                                          ('group_id', '=', group.id)])

        query_res = []
        if account_ids:
            if len(account_ids.ids) == 1:
                z = "(" + str(account_ids.id) + ")"
            else:
                z = tuple(account_ids.ids)

            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "

            self._cr.execute("""
            SELECT
                aml.account_id as account_id,
                sum(aml.current_year_mtd) AS CYMTD,
                sum(aml.previous_year_mtd) AS PYMTD,
                sum(aml.current_year_ytd) AS CYYTD,
                sum(aml.previous_year_ytd) AS PYYTD
            from (
                SELECT
                    account_id,
                    case
                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                        AND (ml.date <= date_trunc('day', timestamp '%s')::date)
                        THEN sum(credit-debit)
                        ELSE
                        0.00
                    end as previous_year_mtd,

                    case
                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                        AND (ml.date <= date_trunc('day', timestamp '%s')::date)
                        THEN sum(credit-debit)
                        ELSE
                        0.00
                    end as current_year_mtd,

                    case
                        when (ml.date >= date_trunc('year',timestamp '%s')::date)
                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                        THEN sum(credit-debit)
                        ELSE
                        0.00
                        end as current_year_ytd,

                    case
                        when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                        THEN sum(credit-debit)
                        ELSE
                        0.00
                        end as previous_year_ytd

                FROM
                    account_move_line as ml
                    %s
                    where user_type_id in %s AND ml.company_id = %s
                    AND account_id in %s
                    AND my_acc_group_id = %s
                    %s

                GROUP BY 
                    account_id,ml.date
                ) as aml

            GROUP BY

            account_id
            """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, tuple(account_type_id.ids), record.company_id.id, z, group.id, new_target_move))
            query_res = self._cr.fetchall()
        return query_res

    # 2nd page report
    def get_exp_analytic_account_value(self, record):
        account_type_id = self.env.ref('account.data_account_type_expenses')
        group_id = self.env.ref('sbk_group.account_group_main_8')

        group_child_ids = self.env['account.group'].search([('parent_id', '=', group_id.id)]).ids
        group_child_ids.append(group_id.id)

        account_ids = self.env['account.account'].search([('company_id', '=', record.company_id.id),
                                                          ('group_id', 'in', group_child_ids)])

        query_res = []
        if account_ids:
            if len(account_ids.ids) == 1:
                z = "(" + str(account_ids.id) + ")"
            else:
                z = tuple(account_ids.ids)

            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "

            date = record.date
            strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
            strp_d = strp_dt.date()
            py_dt = strp_d + rd(years=-1)
            if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
                py_dt += rd(day=29)
            py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            self._cr.execute("""
                        SELECT
                            aml.analytic_acc_group_id as analytic_group_id,
                            sum(aml.current_year_mtd) AS CYMTD,
                            sum(aml.previous_year_mtd) AS PYMTD,
                            sum(aml.current_year_ytd) AS CYYTD,
                            sum(aml.previous_year_ytd) AS PYYTD
                        from (
                            SELECT
                                analytic_acc_group_id,
                                case
                                    when (ml.date >= date_trunc('month',timestamp '%s')::date)
                                    AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                    THEN sum(ml.debit-ml.credit)
                                    ELSE
                                    0.00
                                end as previous_year_mtd,

                                case
                                    when (ml.date >= date_trunc('month', timestamp '%s')::date)
                                    AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                    THEN sum(ml.debit-ml.credit)
                                    ELSE
                                    0.00
                                end as current_year_mtd,

                                case
                                    when (ml.date >= date_trunc('year',timestamp '%s')::date)
                                    AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                    THEN sum(ml.debit-ml.credit)
                                    ELSE
                                    0.00
                                end as current_year_ytd,

                                case
                                    when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                                    AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                    THEN sum(ml.debit-ml.credit)
                                    ELSE
                                    0.00
                                end as previous_year_ytd

                            FROM
                                account_move_line as ml
                                %s
                                where user_type_id = %s AND ml.company_id = %s
                                AND analytic_acc_group_id is not null
                                %s

                            GROUP BY

                                analytic_acc_group_id,ml.date
                            ) as aml

                        GROUP BY

                        analytic_acc_group_id
                """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, account_type_id.id, record.company_id.id, new_target_move))

            query_res = self._cr.fetchall()
        return query_res

    def group_wise_analytic_account_value(self, record, group):
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        anaylytic_obj = self.env['account.analytic.account']
        analytic_account_ids = anaylytic_obj.search([('company_id', '=', record.company_id.id), ('analytic_group_id', '=', group.id)]).ids
        if analytic_account_ids:
            if len(analytic_account_ids) == 1:
                z = "(" + str(analytic_account_ids[0]) + ")"
            else:
                z = tuple(analytic_account_ids)

            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "

            account_type_id = self.env.ref('account.data_account_type_expenses')
            self._cr.execute("""
                            SELECT
                                aml.analytic_account_id as analytic_account_id,
                                sum(aml.current_year_mtd) AS CYMTD,
                                sum(aml.previous_year_mtd) AS PYMTD,
                                sum(aml.current_year_ytd) AS CYYTD,
                                sum(aml.previous_year_ytd) AS PYYTD
                            from (
                                SELECT
                                    analytic_account_id,
                                    case
                                        when (ml.date >= date_trunc('month',timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                    end as previous_year_mtd,

                                    case
                                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                    end as current_year_mtd,

                                    case
                                        when (ml.date >= date_trunc('year',timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                    end as current_year_ytd,

                                    case
                                        when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as previous_year_ytd

                                    FROM
                                    account_move_line as ml
                                    %s
                                    where user_type_id = %s AND ml.company_id = %s
                                    AND analytic_account_id is not null
                                    AND analytic_account_id in %s
                                    %s
                                GROUP BY 
                                    analytic_account_id,ml.date
                                ) as aml
                                LEFT JOIN account_analytic_account analytic_acc ON
                                (analytic_acc.id = aml.analytic_account_id)
    
                            GROUP BY
                            analytic_account_id,analytic_acc.sequence

                            ORDER BY 
                            analytic_acc.sequence

                    """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, account_type_id.id, record.company_id.id, z, new_target_move,))
            query_res = self._cr.fetchall()
            return query_res

    # 3rd Page Report
    def analytic_grp_acc_wise_report(self, record, acc_group, analytic_acc_grp):
        account_type_id = self.env.ref('account.data_account_type_expenses')
        account_obj = self.env['account.account']
        account_group_obj = self.env['account.group']
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        account_ids = account_obj.search([('company_id', '=', record.company_id.id),
                                          ('group_id', '=', acc_group.id)])

        query_res = []
        account_wise_total = {}
        for account in account_ids:
            account_wise_total.setdefault(account, [])
#         if account_ids:
#             if len(account_ids.ids) == 1:
#                 z = "(" + str(account_ids.id) + ")"
#             else:
#                 z = tuple(account_ids.ids)

            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "
    
            self._cr.execute("""
                            SELECT
                                coalesce(sum(aml.current_year_mtd),0)  AS CYMTD,
                                coalesce(sum(aml.previous_year_mtd),0) AS PYMTD,
                                coalesce(sum(aml.current_year_ytd),0) AS CYYTD,
                                coalesce(sum(aml.previous_year_ytd),0) AS PYYTD
                            from (
                                SELECT
                                    case
                                        when (ml.date >= date_trunc('month',timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as previous_year_mtd,
                                    case
                                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as current_year_mtd,

                                    case
                                        when (ml.date >= date_trunc('year',timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as current_year_ytd,

                                    case
                                        when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as previous_year_ytd
                                FROM
                                    account_move_line as ml
                                    %s
                                    where user_type_id = %s AND ml.company_id = %s
                                    AND account_id = %s
                                    AND analytic_acc_group_id = %s
                                    AND my_acc_group_id = %s
                                    %s
                                GROUP BY 
                                    ml.date
                                ) as aml

                    """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, account_type_id.id, record.company_id.id, account.id, analytic_acc_grp.id, acc_group.id, new_target_move,))
            query_res = self._cr.fetchone()
            account_wise_total[account].extend(query_res)

        return account_wise_total

    # Analytic Group->Account Group wise Total
    def analytic_grp_acc_wise_total(self, record, acc_group, analytic_acc_grp):
        account_type_id = self.env.ref('account.data_account_type_expenses')
        account_obj = self.env['account.account']
        account_group_obj = self.env['account.group']
        date = record.date
        strp_dt = dt_dt.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
            py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        account_ids = account_obj.search([('company_id', '=', record.company_id.id),
                                          ('group_id', '=', acc_group.id)])

        query_res = []
        if account_ids:
            if len(account_ids.ids) == 1:
                z = "(" + str(account_ids.id) + ")"
            else:
                z = tuple(account_ids.ids)

            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "

            self._cr.execute("""
                            SELECT
                                sum(aml.current_year_mtd) AS CYMTD,
                                sum(aml.previous_year_mtd) AS PYMTD,
                                sum(aml.current_year_ytd) AS CYYTD,
                                sum(aml.previous_year_ytd) AS PYYTD
                            from (
                                SELECT
                                    case
                                        when (ml.date >= date_trunc('month',timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as previous_year_mtd,
                                    case
                                        when (ml.date >= date_trunc('month', timestamp '%s')::date)
                                        AND (ml.date <= date_trunc('day',  timestamp '%s')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as current_year_mtd,
                                    case
                                        when (ml.date >= date_trunc('year',timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                        end as current_year_ytd,
                                    case
                                        when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                                        AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                        THEN sum(ml.debit-ml.credit)
                                        ELSE
                                        0.00
                                    end as previous_year_ytd
                                FROM
                                    account_move_line as ml
                                    %s
                                    where user_type_id = %s AND ml.company_id = %s
                                    AND account_id in %s
                                    AND analytic_acc_group_id = %s
                                    AND my_acc_group_id = %s
                                    %s
                                GROUP BY 
                                    ml.date
                                ) as aml

                    """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, account_type_id.id, record.company_id.id, z, analytic_acc_grp.id, acc_group.id, new_target_move,))
            query_res = self._cr.fetchall()
        return query_res

    def find_parent(self, group_id):
        acc_hrp_id = self.env['account.group'].search([('id', '=', group_id.parent_id.id)], limit=1)
        if acc_hrp_id:
            return self.find_parent(acc_hrp_id)
        else:
            return group_id

    # 4th Page Report
    def analytic_acc_wise_report(self, record, group , analytic_acc):
        account_type_id = self.env.ref('account.data_account_type_expenses')
        group_id = self.env.ref('sbk_group.account_group_main_8')
        account_obj = self.env['account.account']
        account_group_obj = self.env['account.group']
        account_analytic_account_obj = self.env['account.analytic.account']
        date = record.date
        strp_dt = dt_dt.strptime(date,DEFAULT_SERVER_DATE_FORMAT)
        strp_d = strp_dt.date()
        py_dt = strp_d + rd(years=-1)
        if py_dt.month == 2 and py_dt.day == 28 and calendar.isleap(py_dt.year):
                py_dt += rd(day=29)
        py_date = py_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        account_ids = self.env['account.account'].sudo().search([('company_id', '=', record.company_id.id),
                                                                 ('group_id', '=', group.id),
                                                                 ])

        query_res = []
        account_wise_total = {}

#         account_ids = []
#         for lines in analytic_acc.line_ids.filtered(lambda l:l.general_account_id):
#             account_ids.append(lines.general_account_id.id)
#             account_ids = list(set(account_ids))

#         query_res = []
#         if account_ids:
#             if len(account_ids) == 1:
#                 z = "(" + str(account_ids[0]) + ")"
#             else:
#                 z = tuple(account_ids)

        for account in account_ids:
            account_wise_total.setdefault(account, [])
            target_move = ''
            new_target_move = ''
            if record.target_move != 'all':
                target_move = "LEFT JOIN account_move m ON (m.id=ml.move_id) "
                new_target_move = "AND m.state = 'posted' "

            self._cr.execute("""
                          SELECT
                              coalesce(sum(aml.current_year_mtd),0)  AS CYMTD,
                              coalesce(sum(aml.previous_year_mtd),0) AS PYMTD,
                              coalesce(sum(aml.current_year_ytd),0) AS CYYTD,
                              coalesce(sum(aml.previous_year_ytd),0) AS PYYTD
                          from (
                              SELECT
                                  case
                                      when (ml.date >= date_trunc('month',timestamp '%s')::date)
                                      AND (ml.date <= timestamp '%s'::date)
                                      THEN sum(ml.debit-ml.credit)
                                      ELSE
                                      0.00
                                  end as previous_year_mtd,

                                  case
                                      when (ml.date >= date_trunc('month', timestamp '%s')::date)
                                      AND (ml.date <= timestamp '%s'::date)
                                      THEN sum(ml.debit-ml.credit)
                                      ELSE
                                      0.00
                                  end as current_year_mtd,

                                  case
                                      when (ml.date >= date_trunc('year',timestamp '%s')::date)
                                      AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                      THEN sum(ml.debit-ml.credit)
                                      ELSE
                                      0.00
                                  end as current_year_ytd,

                                  case
                                      when (ml.date >= date_trunc('year',  timestamp '%s')::date)
                                      AND  (ml.date <= ((date_trunc('month',  timestamp '%s') + INTERVAL '1 month') - INTERVAL '1 day')::date)
                                      THEN sum(ml.debit-ml.credit)
                                      ELSE
                                      0.00
                                  end as previous_year_ytd
                              FROM
                                  account_move_line as ml
                                  %s
                                  where user_type_id = %s AND ml.company_id = %s
                                  AND my_acc_group_id = %s
                                  AND account_id = %s
                                  AND analytic_account_id = %s
                                  %s
                              GROUP BY
                                  my_acc_group_id,ml.date
                              ) as aml

                  """ % (py_date, py_date, date, date, date, date, py_date, py_date, target_move, account_type_id.id, record.company_id.id, group.id, account.id, analytic_acc.id, new_target_move,))

            query_res = self._cr.fetchone()
            account_wise_total[account].extend(query_res)
        return account_wise_total
