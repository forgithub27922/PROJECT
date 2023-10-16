# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta

class AccountAuxiliarReport(models.AbstractModel):
    _name = "account.auxiliar.report"
    _description = "Auxiliar Contable"
    _inherit = "account.general.ledger"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_all_entries = False
    filter_journals = True
    filter_analytic = True
    filter_unfold_all = False
    filter_acc_acc = True
    filter_acc_partner = True

    @api.model
    def _get_report_name(self):
        return _("Auxiliar Contable")

    ####################################################
    # OPTIONS: acc_acc
    ####################################################
    @api.model
    def _init_filter_acc_acc(self, options, previous_options=None):
        if not self.filter_acc_acc:
            return
        options['acc_acc'] = True
        options['account_ids'] = previous_options and previous_options.get('account_ids') or []
        selected_account_ids = [int(account) for account in options['account_ids']]
        selected_accounts = selected_account_ids and self.env['account.account'].browse(selected_account_ids) or self.env['account.account']
        options['selected_account_ids'] = selected_accounts.mapped('code')

    @api.model
    def _get_options_acc_acc_domain(self, options):
        domain = []
        if options.get('account_ids'):
            account_ids = [int(account) for account in options['account_ids']]
            domain.append(('account_id', 'in', account_ids))
        return domain

    ####################################################
    # OPTIONS: acc_partners
    ####################################################

    @api.model
    def _init_filter_acc_partner(self, options, previous_options=None):
        if not self.filter_acc_partner:
            return
        options['acc_partner'] = True
        options['acc_partner_ids'] = previous_options and previous_options.get('acc_partner_ids') or []
        selected_acc_partner_ids = [int(partner) for partner in options['acc_partner_ids']]
        selected_acc_partners = selected_acc_partner_ids and self.env['res.partner'].browse(selected_acc_partner_ids) or self.env['res.partner']
        options['selected_acc_partner_ids'] = selected_acc_partners.mapped('name')

    @api.model
    def _get_options_acc_partner_domain(self, options):
        domain = []
        if options.get('acc_partner_ids'):
            acc_partner_ids = [int(partner) for partner in options['acc_partner_ids']]
            domain.append(('partner_id', 'in', acc_partner_ids))
        return domain

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountAuxiliarReport, self)._get_options_domain(options=options)
        domain += self._get_options_acc_acc_domain(options)
        domain += self._get_options_acc_partner_domain(options)
        return domain

    def _set_context(self, options):
        ctx = super(AccountAuxiliarReport, self)._set_context(options=options)
        if options.get('account_ids'):
            ctx['account_ids'] = self.env['account.account'].browse([int(account) for account in options['account_ids']])
        if options.get('acc_partner_ids'):
            ctx['acc_partner_ids'] = self.env['res.partner'].browse([int(partner) for partner in options['acc_partner_ids']])            
        return ctx

    def get_report_informations(self, options):
        info = super(AccountAuxiliarReport, self).get_report_informations(options=options)
        options = info.get('options')
        if options.get('acc_acc'):
            options['selected_account_ids'] = [self.env['account.account'].browse(int(account)).code for account in options['account_ids']]
        if options.get('acc_partner'):
            options['selected_acc_partner_ids'] = [self.env['res.partner'].browse(int(partner)).name for partner in options['acc_partner_ids']]            
        return info

