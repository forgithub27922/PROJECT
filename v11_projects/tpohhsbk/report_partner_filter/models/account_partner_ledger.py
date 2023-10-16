# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, _, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_partner = None

    @api.model
    def get_options(self, previous_options=None):
        if self.filter_partner:
            self.filter_partners = [] if self.filter_partner else None
        return super(AccountReport, self).get_options(previous_options)

    def set_context(self, options):
        # Set partners in in context
        ctx = super(AccountReport, self).set_context(options)
        if options.get('partners'):
            ctx['partners_ids'] = self.env['res.partner'].browse([int(p) for p in options['partners']])
        return ctx

    @api.multi
    def get_report_informations(self, options):
        '''
        Inherit: return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        partner_obj = self.env['res.partner'].sudo()
        options = self.get_options(options)

        # apply date and date_comparison filter
        options = self.apply_date_filter(options)
        options = self.apply_cmp_filter(options)

        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        if options.get('analytic') is not None:
            searchview_dict['analytic_accounts'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.account'].search([])] or False
            searchview_dict['analytic_tags'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.tag'].search([])] or False

        # List out all partners list
        if options.get('partner') is not None:
            query = '''
                SELECT account_move_line.partner_id
                FROM account_move as account_move_line__move_id, account_move_line
                LEFT JOIN account_account ac ON (ac.id = account_move_line.account_id)
                WHERE (account_move_line.move_id=account_move_line__move_id.id)
                AND account_move_line.partner_id IS NOT NULL
            '''
            # Partner Ledger Date Filter
            if options.get('date', False):
                if options['date'].get('date_from', False):
                    query += " AND account_move_line.date_maturity >= '%s'" % options['date'].get('date_from')
                if options['date'].get('date_to', False):
                    query += " AND account_move_line.date_maturity <= '%s'" % options['date'].get('date_to')
                # Aged Receivable/Payable Date Filter
                if options['date'].get('date', False):
                    query += " AND account_move_line.date <= '%s'" % options['date'].get('date')

            # Partner Ledger Account Type Filter
            if options.get('account_type', False):
                account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
                if not account_types:
                    account_types = [a.get('id') for a in options.get('account_type')]
                if len(account_types) == 1:
                    query += " AND ac.internal_type = '%s'" % account_types[0]
                else: query += " AND ac.internal_type IN %s" % str(tuple(account_types))

            # Aged Receivable/Payable Account Type Filter
            if self._context.get('model', False):
                if self._context.get('model') == 'account.aged.receivable':
                    query += " AND ac.internal_type = 'receivable'"
                elif self._context.get('model') == 'account.aged.payable':
                    query += " AND ac.internal_type = 'payable'"

            if options.get('unreconciled'):
                query += ' AND account_move_line.full_reconcile_id IS NULL'
            query += ' GROUP BY account_move_line.partner_id'
            self.env.cr.execute(query)
            partners = partner_obj.browse()
            for val in self.env.cr.fetchall():
                partners += partner_obj.browse(val and val[0] or False)
            searchview_dict['partners'] = [(p.id, p.name) for p in partners] or False

        report_manager = self.get_report_manager(options)
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self.get_reports_buttons(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view'].render_template(self.get_templates().get('search_template', 'account_report.search_template'), values=searchview_dict),
                }
        return info


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    filter_partner = True

    def get_columns_name(self, options):
        hide_col_setting_rec = self.env['ir.config_parameter'].sudo().get_param(
                'partner_ledger_hide_columns')
        if hide_col_setting_rec:
            return [
                {},
                {'name': _('JRNL')},
                {'name': _('Ref')},
                {'name': _('Initial Balance'), 'class': 'number'},
                {'name': _('Debit'), 'class': 'number'},
                {'name': _('Credit'), 'class': 'number'},
                {'name': _('Balance'), 'class': 'number'},
            ]
        return super(ReportPartnerLedger, self).get_columns_name(options)

    def do_query(self, options, line_id):
        ''' Inherit to set condition in query based on selected partners. '''
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

#         Selected partners filter in query (WHERE clause)
        if options.get('partners'):
            if len(options.get('partners')) == 1:
                line_clause += ' AND \"account_move_line\".partner_id = ' + str(options.get('partners')[0])
            else:
                line_clause += ' AND \"account_move_line\".partner_id in ' + str(tuple(map(int, options.get('partners'))))

        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        results = dict([(k[0], {'balance': k[1], 'debit': k[2], 'credit': k[3]}) for k in results])
        return results

    def group_by_partner_id(self, options, line_id):
        ''' Inherit to set domain based on selected partners. '''
        partners = {}
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        date_from = options['date']['date_from']
        results = self.do_query(options, line_id)
        initial_bal_date_to = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=-1)
        initial_bal_results = self.with_context(date_from=False, date_to=initial_bal_date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)).do_query(options, line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids']), ('account_id.internal_type', 'in', account_types)]
        base_domain.append(('date', '>=', date_from))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if options.get('unreconciled'):
            base_domain.append(('full_reconcile_id', '=', False))

        # Selected partners filter in domain
        if context.get('partner_ids'):
            base_domain += [('partner_id', 'in', context['partner_ids'].ids)]

        for partner_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('partner_id', '=', partner_id))
            partner = self.env['res.partner'].browse(partner_id)
            partners[partner] = result
            partners[partner]['initial_bal'] = initial_bal_results.get(partner.id, {'balance': 0, 'debit': 0, 'credit': 0})
            partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
            if not context.get('print_mode'):
                #  fetch the 81 first amls. The report only displays the first 80 amls. We will use the 81st to know if there are more than 80 in which case a link to the list view must be displayed.
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date', limit=81)
            else:
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date')
        return partners

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        if line_id:
            line_id = line_id.replace('partner_', '')
        context = self.env.context

        #If a default partner is set, we only want to load the line referring to it.
        if options.get('partner_id'):
            line_id = options['partner_id']

        # If hide columns(Account, Matching Number) configuration is set (Customize)
        hide_col_setting_rec = self.env['ir.config_parameter'].sudo().get_param(
                'partner_ledger_hide_columns')

        grouped_partners = self.group_by_partner_id(options, line_id)
        sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines') or options.get('partner_id')
        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner in sorted_partners:
            debit = grouped_partners[partner]['debit']
            credit = grouped_partners[partner]['credit']
            balance = grouped_partners[partner]['balance']
            initial_balance = grouped_partners[partner]['initial_bal']['balance']
            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            if hide_col_setting_rec:
                lines.append({
                    'id': 'partner_' + str(partner.id),
                    'name': partner.name,
                    'columns': [{'name': v} for v in [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                    'level': 2,
                    'trust': partner.trust,
                    'unfoldable': True,
                    'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 3,
                })
            else: 
                lines.append({
                    'id': 'partner_' + str(partner.id),
                    'name': partner.name,
                    'columns': [{'name': v} for v in [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                    'level': 2,
                    'trust': partner.trust,
                    'unfoldable': True,
                    'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 5,
                })
            if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
                progress = initial_balance
                domain_lines = []
                amls = grouped_partners[partner]['lines']
                too_many = False
                if len(amls) > 80 and not context.get('print_mode'):
                    amls = amls[-80:]
                    too_many = True
                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    progress_before = progress
                    progress = progress + line_debit - line_credit
                    name = '-'.join(
                        (line.move_id.name not in ['', '/'] and [line.move_id.name] or []) +
                        (line.ref not in ['', '/', False] and [line.ref] or []) +
                        ([line.name] if line.name and line.name not in ['', '/'] else [])
                    )
                    if len(name) > 35 and not self.env.context.get('no_format'):
                        name = name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    if hide_col_setting_rec:
                        domain_lines.append({
                            'id': line.id,
                            'parent_id': 'partner_' + str(partner.id),
                            'name': line.date,
                            'columns': [{'name': v} for v in [line.journal_id.code, name, self.format_value(progress_before),
                                        line_debit != 0 and self.format_value(line_debit) or '',
                                        line_credit != 0 and self.format_value(line_credit) or '',
                                        self.format_value(progress)]],
                            'caret_options': caret_type,
                            'level': 4,
                        })
                    else:
                        domain_lines.append({
                            'id': line.id,
                            'parent_id': 'partner_' + str(partner.id),
                            'name': line.date,
                            'columns': [{'name': v} for v in [line.journal_id.code, line.account_id.code, name, line.full_reconcile_id.name, self.format_value(progress_before),
                                        line_debit != 0 and self.format_value(line_debit) or '',
                                        line_credit != 0 and self.format_value(line_credit) or '',
                                        self.format_value(progress)]],
                            'caret_options': caret_type,
                            'level': 4,
                        })
                if too_many:
                    if hide_col_setting_rec:
                        domain_lines.append({
                            'id': 'too_many_' + str(partner.id),
                            'parent_id': 'partner_' + str(partner.id),
                            'action': 'view_too_many',
                            'action_id': 'partner,%s' % (partner.id,),
                            'name': _('There are more than 80 items in this list, click here to see all of them'),
                            'colspan': 6,
                            'columns': [{}],
                        })
                    else:
                        domain_lines.append({
                            'id': 'too_many_' + str(partner.id),
                            'parent_id': 'partner_' + str(partner.id),
                            'action': 'view_too_many',
                            'action_id': 'partner,%s' % (partner.id,),
                            'name': _('There are more than 80 items in this list, click here to see all of them'),
                            'colspan': 8,
                            'columns': [{}],
                        })
                lines += domain_lines
        if not line_id:
            if hide_col_setting_rec:
                lines.append({
                    'id': 'grouped_partners_total',
                    'name': _('Total'),
                    'level': 0,
                    'class': 'o_account_reports_domain_total',
                    'columns': [{'name': v} for v in ['', '', self.format_value(total_initial_balance), self.format_value(total_debit), self.format_value(total_credit), self.format_value(total_balance)]],
                })
            else:
                lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in ['', '', '', '', self.format_value(total_initial_balance), self.format_value(total_debit), self.format_value(total_credit), self.format_value(total_balance)]],
            })
        return lines
