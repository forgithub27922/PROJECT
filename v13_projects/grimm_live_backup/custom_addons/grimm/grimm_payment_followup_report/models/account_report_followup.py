#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import logging
from openerp.tools.translate import _
from datetime import datetime
from openerp import models, fields, api, tools

from openerp.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.misc import formatLang
from odoo.tools import config
import lxml.html
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta
import time
import ast
import math
from odoo.tools.misc import formatLang, format_date, get_lang

_logger = logging.getLogger(__name__)

COLLECTION_NAME = "basic"
COLLECTION_VERSION = "1.0.0"

class report_account_followup_report(models.AbstractModel):
    _inherit = "account.followup.report"

    def get_follow_up_line(self,options):
        return self._get_lines(options)

    def _get_mahnung_contact(self, partner):
        if partner.send_mahnung:
            return partner
        for child in partner.child_ids:
            if child.send_mahnung:
                return child
        return self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice'])

    @api.model
    def send_email(self, options):
        """
        Inherited just to get related partner email based on boolean field 'send_mahnung'
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        non_blocked_amls = partner.unreconciled_aml_ids.filtered(lambda aml: not aml.blocked)
        if not non_blocked_amls:
            return True
        non_printed_invoices = partner.unpaid_invoices.filtered(lambda inv: not inv.message_main_attachment_id)
        if non_printed_invoices and partner.followup_level.join_invoices:
            raise UserError(
                _('You are trying to send a followup report to a partner for which you didn\'t print all the invoices ({})').format(
                    " ".join(non_printed_invoices.mapped('name'))))
        # GRIMM START
        # invoice_partner = self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice'])
        invoice_partner = self._get_mahnung_contact(partner)
        # GRIMM END

        email = invoice_partner.email
        options['keep_summary'] = True
        if email and email.strip():
            # When printing we need te replace the \n of the summary by <br /> tags
            body_html = self.with_context(print_mode=True, mail=True, lang=partner.lang or self.env.user.lang).get_html(
                options)
            body_html = body_html.replace(b'o_account_reports_edit_summary_pencil',
                                          b'o_account_reports_edit_summary_pencil d-none')
            start_index = body_html.find(b'<span>', body_html.find(b'<div class="o_account_reports_summary">'))
            end_index = start_index > -1 and body_html.find(b'</span>', start_index) or -1
            if end_index > -1:
                replaced_msg = body_html[start_index:end_index].replace(b'\n', b'')
                body_html = body_html[:start_index] + replaced_msg + body_html[end_index:]
            partner.with_context(mail_post_autofollow=True).message_post(
                partner_ids=[invoice_partner.id],
                body=body_html,
                subject=_('%s Payment Reminder') % (self.env.company.name) + ' - ' + partner.name,
                subtype_id=self.env.ref('mail.mt_note').id,
                model_description=_('payment reminder'),
                email_layout_xmlid='mail.mail_notification_light',
                attachment_ids=partner.followup_level.join_invoices and partner.unpaid_invoices.message_main_attachment_id.ids or [],
                mail_server_id = 9, # As per suggestion from Tobias set buchaltung server as default.
            )
            return True
        raise UserError(
            _('Could not send mail to partner %s because it does not have any email address defined') % partner.display_name)

    def _get_columns_name(self, options):
        is_mail = self.env.context.get('mail', False)
        headers = [
                {'name': "Rechnungsnummer" if is_mail else _(' ReNr. '), 'style': 'font-weight: bold; font-size: 16px; width: 25%;' if is_mail else 'text-align:left; white-space:nowrap;font-size:15px;'},
                {'name': _(' Date '), 'class': 'date', 'style': 'text-align: center; font-size: 16px; width: 25%;' if is_mail else 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _(' Due Date '), 'class': 'date', 'style': 'font-weight: bold; text-align: center; font-size: 16px; width: 25%;' if is_mail else 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _(' Seit Tagen '), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _(' Belegart '), 'style': 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _('Communication'), 'style': 'text-align:right; white-space:nowrap;font-size:15px;'},
                {'name': _(' Expected Date '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _(' Excluded '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;font-size:15px;'},
                {'name': _(' Mahnbetrag '), 'class': 'number', 'style': 'text-align: right; font-size: 16px; width: 25%;' if is_mail else 'text-align:right; white-space:nowrap;font-size:15px;'}
                ]
        if self.env.context.get('print_mode'):
            headers = headers[:6] + headers[8:]
        if self.env.context.get('mail',False):
            headers = headers[:3] + headers[-1:]
        return headers

    def _get_lines(self, options, line_id=None):
        """
        Override
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0

        aged_filter = self.env['partner.aged.filter'].search([], limit=1)
        move_filter_ids = []
        if aged_filter:
            import ast
            domain = ast.literal_eval(aged_filter.name)
            if domain:
                move_filter_ids = self.env['account.move'].sudo().search(domain).ids

        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
            if l.company_id == self.env.company and l.move_id.id in move_filter_ids:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            is_mail = self.env.context.get('mail', False)
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                a = datetime.strptime(str(aml.date), "%Y-%m-%d")
                b = datetime.strptime(str(aml.date_maturity or aml.date), "%Y-%m-%d")
                delta = b - a
                since = delta.days
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': '%s date'%'' if is_mail else 'color-red', 'style': 'white-space:nowrap;text-align:center;'}
                if is_payment:
                    date_due = ''
                move_line_name = aml.move_id.name or aml.name
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date, lang_code=lang_code) if aml.expected_pay_date else ''
                # columns = [
                #     format_date(self.env, aml.date, lang_code=lang_code),
                #     date_due,
                #     str(since),
                #     aml.move_id.invoice_origin or '',
                #     move_line_name,
                #     (expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
                #     {'name': '', 'blocked': aml.blocked},
                #     amount,
                # ]
                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    date_due, str(since),
                    str(is_payment and 'Gutschrift' or 'Rechnung'),
                    move_line_name,
                    (expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
                    {'name': aml.blocked, 'blocked': aml.blocked},
                    amount
                ]


                if self.env.context.get('print_mode'):
                    #columns = columns[:4] + columns[6:]
                    columns = columns[:5] + columns[7:]
                if is_mail:
                    columns = columns[:2] + columns[-1:]
                if is_overdue:
                    lines.append({
                        'id': aml.id,
                        'account_move': aml.move_id,
                        'name': aml.move_id.name,
                        'caret_options': 'followup',
                        'style':'font-family: arial,helvetica,sans-serif; line-height: 21px; font-size: 16px;' if is_mail else '',
                        'move_id': aml.move_id.id,
                        'type': is_payment and 'payment' or 'unreconciled_aml',
                        'unfoldable': False,
                        'columns': [type(v) == dict and v or {'name': v} for v in columns],
                    })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1

            total_col = 6
            if self.env.context.get('print_mode'):
                total_col = 4
            if self.env.context.get('mail'):
                total_col = 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'extra_charge total',
                'style': 'border-top-style: double;%s'%('font-family: arial,helvetica,sans-serif; line-height: 21px; font-weight: bold; font-size: 16px; padding-top: 5px; padding-bottom: 5px;' if total >= 0 else ''),
                'unfoldable': False,
                'level': 6,
                #'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [total >= 0 and _('Total Due') or '', total_due]],
                'columns': [{'name': v} for v in [''] * (total_col) + [total >= 0 and _('Mahngebühren') or '', formatLang(self.env, 5, currency_obj=currency)]],
            })
            if total_issued > 0:
                total_issued = total_issued + 5
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'style':'font-family: arial,helvetica,sans-serif; line-height: 21px; font-weight: bold; font-size: 16px; padding-top: 5px; padding-bottom: 5px; text-decoration: underline; color: red;',
                    'level': 3,
                    'columns': [{'name': v} for v in [''] * (total_col) + [_('Total Overdue'), total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()
        return lines

    def get_html(self, options, line_id=None, additional_context=None):
        """
        Override
        Compute and return the content in HTML of the followup for the partner_id in options
        """
        if additional_context is None:
            additional_context = {}
            additional_context['followup_line'] = self.get_followup_line(options)
            if additional_context.get('followup_line', False):
                additional_context['company_info'] = additional_context['followup_line'].company_id
        partner = self.env['res.partner'].browse(options['partner_id'])
        additional_context['partner'] = partner
        additional_context['lang'] = partner.lang or get_lang(self.env).code
        additional_context['invoice_address_id'] = self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice'])
        additional_context['today'] = fields.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return super(report_account_followup_report, self).get_html(options, line_id=line_id, additional_context=additional_context)

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def get_pdf(self, options, minimal_layout=True):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )
        body_html = self.with_context(print_mode=True).get_html(options)

        body = body.replace(b'<body class="o_account_reports_body_print">',
                            b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            footer = ''
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            header = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                   values=dict(rcontext, subst=True, body=header))
        else:
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
            })
            header = self.env['ir.actions.report'].render_template("web.external_layout", values=rcontext)
            header = header.decode('utf-8')  # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {}
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                            values=dict(rcontext, subst=True,
                                                                                        body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                           values=dict(rcontext, subst=True,
                                                                                       body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header.encode()
                footer = b''
            header = headers

        landscape = False
        if len(self.with_context(print_mode=True).get_header(options)[-1]) > 5:
            landscape = True
        landscape_data = self.env['ir.config_parameter'].get_param('is_followup_report_landscape', default=False)
        if landscape_data.upper() == "TRUE":
            landscape = True
        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header, footer=footer,
            landscape=landscape,
            specific_paperformat_args=spec_paperformat_args
        )

class ResCompany(models.Model):
    _inherit = "res.company"

    interval_days = fields.Integer(string='Days Interval for Aged Receivable', default=30)
    number_of_columns = fields.Integer(string='Number of Columns', default=5)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    interval_days = fields.Integer(related='company_id.interval_days', string='Interval Days')
    number_of_columns = fields.Integer(related='company_id.number_of_columns', string='Number of Columns')


class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"

    filter_date = {'mode': 'single', 'filter': 'today'}
    filter_unfold_all = False
    filter_partner = True
    order_selected_column = {'default': 0}

    def _get_columns_name(self, options):
        # Grimm START
        filter = self.env['partner.aged.filter'].search([], limit=1)
        duration = filter.duration if filter else 30
        range_list = []
        last_number = 0
        for i in range(4):
            range_list.append("%s - %s"%(last_number+1, last_number+duration))
            last_number += duration
        # Grimm END
        columns = [
            {},
            {'name': _("Followup Level"), 'class': '', 'style': 'text-align:center;white-space:nowrap;'},
            {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': range_list[0], 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': range_list[1], 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': range_list[2], 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': range_list[3], 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        filter = self.env['partner.aged.filter'].search([], limit=1)
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            partner_id_str = line_id.split('_')[1]
            if partner_id_str.isnumeric():
                partner_id = self.env['res.partner'].browse(int(partner_id_str))
            else:
                partner_id = False
            context.update(partner_ids=partner_id)
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(
            **context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', filter.duration if filter else 30)

        for values in results:
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': aml.partner_id.followup_level.name or ''}]+[{'name': v} for v in
                                    [format_date(self.env, aml.date_maturity or aml.date), aml.journal_id.code,
                                     aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for
                                    v in [line['period'] == 7 - i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in
                                                 [total[6], total[4], total[3], total[2], total[1], total[0],
                                                  total[5]]],
            }
            lines.append(total_line)
        return lines

class ReportAgedPartnerBalance(models.AbstractModel):

    _name = 'report.account.report_agedpartnerbalance'
    _description = 'Aged Partner Balance Report'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        #Grimm START
        move_ids = []
        aged_filter = self.env['partner.aged.filter'].search([], limit=1)
        if aged_filter:
            domain = ast.literal_eval(aged_filter.name)
            if domain:
                move_ids = self.env['account.move'].sudo().search(domain).ids
                if len(move_ids) == 1:
                    move_ids.append(0)
                if move_ids:
                    partner_clause += 'AND (l.move_id IN %s)'%(tuple(move_ids),)
                else:
                    partner_clause += 'AND l.move_id < 0'
        # Grimm END
        query = '''
            SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
            FROM account_move_line AS l
              LEFT JOIN res_partner ON l.partner_id = res_partner.id
              LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
              account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (
                        l.reconciled IS NOT TRUE
                        OR EXISTS (
                            SELECT id FROM account_partial_reconcile where max_date > %s
                            AND (credit_move_id = l.id OR debit_move_id = l.id)
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)
            '''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        lines[False] = []
        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = [x[0] for x in cr.fetchall()]
            # prefetch the fields that will be used; this avoid cache misses,
            # which look up the cache to determine the records to read, and has
            # quadratic complexity when the number of records is large...
            move_lines = self.env['account.move.line'].browse(aml_ids)
            move_lines._read(['partner_id', 'company_id', 'balance', 'matched_debit_ids', 'matched_credit_ids'])
            move_lines.matched_debit_ids._read(['max_date', 'company_id', 'amount'])
            move_lines.matched_credit_ids._read(['max_date', 'company_id', 'amount'])
            for line in move_lines:
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from, round = False)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)

                line_amount = user_currency.round(line_amount)
                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from, round = False)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
            line_amount = user_currency.round(line_amount)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                name = partner['name'] or ''
                values['name'] = len(name) >= 45 and not self.env.context.get('no_format') and name[0:41] + '...' or name
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        return res, total, lines

