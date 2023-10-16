# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_is_zero


class ReportAccountGenericTaxTeport(models.AbstractModel):
    _inherit = "account.generic.tax.report"

    def _compute_from_amls(self, options, taxes, period_number):
        sql = self._sql_from_amls_one()
        if options.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()

        # Add: For filter account.
        if options.get('acc_tags'):
            intlist = [int(s_tags) for s_tags in options.get('acc_tags')]
            account_lst = ','.join(map(str, intlist))
            where_clause += ' AND \"account_move_line\".account_id in (%s)' \
                          % (account_lst)

        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['periods'][period_number]['tax'] = result[1]
                taxes[result[0]]['show'] = True
        sql = self._sql_from_amls_two()
        if options.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['periods'][period_number]['net'] = result[1]
                taxes[result[0]]['show'] = True


class ReportGeneralLedger(models.AbstractModel):
    _inherit = "account.general.ledger"

    def _do_query(self, options, line_id, group_by_account=True, limit=False):
        if group_by_account:
            select = "SELECT \"account_move_line\".account_id"
            select += ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_currency),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
            if options.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis').replace('balance', 'balance_cash_basis')
        else:
            select = "SELECT \"account_move_line\".id"
        sql = "%s FROM %s WHERE %s%s"
        if group_by_account:
            sql +=  "GROUP BY \"account_move_line\".account_id"
        else:
            sql += " GROUP BY \"account_move_line\".id"
            sql += " ORDER BY MAX(\"account_move_line\".date),\"account_move_line\".id"
            if limit and isinstance(limit, int):
                sql += " LIMIT " + str(limit)
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''

        # Add: For filter account.
        if options.get('acc_tags'):
            intlist = [int(s_tags) for s_tags in options.get('acc_tags')]
            account_lst = ','.join(map(str, intlist))
            line_clause = ' AND \"account_move_line\".account_id in (%s)' \
                           % (account_lst)

        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        return results

    def group_by_account_id(self, options, line_id):
        accounts = {}
        results = self.do_query(options, line_id)
        initial_bal_date_to = datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d") + timedelta(days=-1)
        initial_bal_results = self.with_context(date_to=initial_bal_date_to.strftime('%Y-%m-%d')).do_query(options, line_id)
        context = self.env.context

        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d"))['date_from'] + timedelta(days=-1)
        unaffected_earnings_per_company = {}
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            unaffected_earnings_per_company[company] = self.with_context(date_to=last_day_previous_fy.strftime('%Y-%m-%d'), date_from=False).do_query_unaffected_earnings(options, line_id, company)

        unaff_earnings_treated_companies = set()
        unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
        for account_id, result in results.items():
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['balance'] = result['debit'] - result['credit']
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id, {'balance': 0, 'amount_currency': 0, 'debit': 0, 'credit': 0})

            if account.user_type_id == unaffected_earnings_type and account.company_id not in unaff_earnings_treated_companies:
                #add the benefit/loss of previous fiscal year to unaffected earnings accounts
                unaffected_earnings_results = unaffected_earnings_per_company[account.company_id]
                for field in ['balance', 'debit', 'credit']:
                    accounts[account]['initial_bal'][field] += unaffected_earnings_results[field]
                    accounts[account][field] += unaffected_earnings_results[field]
                unaff_earnings_treated_companies.add(account.company_id)
            #use query_get + with statement instead of a search in order to work in cash basis too
            aml_ctx = {}
            if context.get('date_from_aml'):
                aml_ctx = {
                    'strict_range': True,
                    'date_from': context['date_from_aml'],
                }
            aml_ids = self.with_context(**aml_ctx)._do_query(options, account_id, group_by_account=False)
            aml_ids = [x[0] for x in aml_ids]
            accounts[account]['lines'] = self.env['account.move.line'].browse(aml_ids)

        # For each company, if the unaffected earnings account wasn't in the selection yet: add it manually
        user_currency = self.env.user.company_id.currency_id
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            if company not in unaff_earnings_treated_companies and not float_is_zero(unaffected_earnings_per_company[company]['balance'], precision_digits=user_currency.decimal_places) and not options.get('acc_tags'):
                unaffected_earnings_account = self.env['account.account'].search([
                    ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', '=', company.id)
                ], limit=1)
                if unaffected_earnings_account and (not line_id or unaffected_earnings_account.id == line_id):
                    accounts[unaffected_earnings_account[0]] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['initial_bal'] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['lines'] = []
        return accounts

class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    def do_query(self, options, line_id):
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        select = ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
        if options.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        sql = "SELECT \"account_move_line\".partner_id%s FROM %s WHERE %s%s AND \"account_move_line\".partner_id IS NOT NULL GROUP BY \"account_move_line\".partner_id"
        tables, where_clause, where_params = self.env['account.move.line']._query_get([('account_id.internal_type', 'in', account_types)])
        line_clause = line_id and ' AND \"account_move_line\".partner_id = ' + str(line_id) or ''

        if options.get('unreconciled'):
            line_clause += ' AND \"account_move_line\".full_reconcile_id IS NULL'

        #Add: For filter account.
        if options.get('acc_tags'):
            intlist = [int(s_tags) for s_tags in options.get('acc_tags')]
            account_lst = ','.join(map(str, intlist))
            line_clause += ' AND \"account_move_line\".account_id in (%s)' \
                           %(account_lst)
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        results = dict([(k[0], {'balance': k[1], 'debit': k[2], 'credit': k[3]}) for k in results])
        return results


class report_account_coa(models.AbstractModel):
    _inherit = "account.coa.report"

    @api.model
    def get_lines(self, options, line_id=None):
        """
        Overwritten method to filter data according to selection of 
        Accounting Tags.
        """
        tag_list = options.get('acc_tags',[])
        # here converting string of ids into integer form.
        tag_list = list(map(int, tag_list or []))
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = {}
        initial_balances = {}
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods') or []

        #get the balance of accounts for each period
        period_number = 0
        for period in reversed(comparison_table):
            res = self.with_context(date_from_aml=period['date_from'], date_to=period['date_to'], date_from=period['date_from'] and company_id.compute_fiscalyear_dates(datetime.strptime(period['date_from'], "%Y-%m-%d"))['date_from'] or None).group_by_account_id(options, line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
            if period_number == 0:
                initial_balances = dict([(k, res[k]['initial_bal']['balance']) for k in res])
            for account in res:
                flag = False
                acc_tags_list = [account.id] #account.tag_ids.ids instad tag create list of accout ids
                # Checking whether specific account contain any tag 
                # from selected tags.if yes then flag will be true. 
                flag = any(a_tag in tag_list for a_tag in acc_tags_list)
                # control will go inside if tag list is blank means first time
                # report page is loading or flag is true.
                if not tag_list or flag:
                    if account not in grouped_accounts:
                        grouped_accounts[account] = [{'balance': 0, 'debit': 0, 'credit': 0} for p in comparison_table]
                    grouped_accounts[account][period_number]['balance'] = res[account]['balance'] - res[account]['initial_bal']['balance']
                    grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - res[account]['initial_bal']['debit']
                    grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - res[account]['initial_bal']['credit']
            period_number += 1
        #build the report
        lines = self._post_process(grouped_accounts, initial_balances, options, comparison_table)
        return lines


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'
 
    @api.multi
    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        report_templ = self.get_templates()
        coa_report_id = self.env.ref('account_reports.template_coa_report')
        current_report = report_templ.get('main_template',False)
        current_report_id = self.env.ref(current_report)
        # Firstly checking if current report is COA report (Trial balance)
        # then only loading custom overwritten method else calling super.

        #with this condition it wil work for Trail balance report only.
        # if current_report_id.id != coa_report_id.id:
        #     return super(AccountReport, self).get_report_informations(options)
        account_tag = False
        if options:
            account_tag = options.get('acc_tags',[])
        options = self.get_options(options)
        # apply date and date_comparison filter
        if options.get('date'):
            options = self.apply_date_filter(options)
            options = self.apply_cmp_filter(options)
 
        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        if options.get('analytic') is not None:
            searchview_dict['analytic_accounts'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.account'].search([])] or False
            searchview_dict['analytic_tags'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.tag'].search([])] or False

        a_tags = self.env['account.account'].sudo().search([('company_id','=',self.env.user.company_id.id)])
        searchview_dict['acc_tags'] = [(p.id, "["+p.code+"] "+p.name)
                                       for p in a_tags] or False
        options['acc_tags'] = [(p.id, p.name) for p in a_tags] or False
        report_manager = self.get_report_manager(options)
        options['acc_tags'] = account_tag
        options['account_tag']=True
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self.get_reports_buttons(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view'].render_template(self.get_templates().get('search_template', 'account_report.search_template'), values=searchview_dict),
                }
        return info

