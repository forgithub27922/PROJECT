# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api

filter_partner_ids = []


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    filter_partner = True


class AccountReportFollowupAll(models.AbstractModel):
    _inherit = "account.followup.report.all"

    def get_partners_in_need_of_action(self, options):
        overdue_only = options.get('type_followup') == 'all'
        ctx = self._context.copy()
        if options and options.get('partners', []):
            ctx.update({'partner_ids': [int(partner) for partner in options.get('partners')]})
        return self.env['res.partner'].with_context(ctx).get_partners_in_need_of_action(overdue_only=overdue_only)

    @api.multi
    def get_report_informations(self, options):
        informations = super(AccountReportFollowupAll, self).get_report_informations(options)
        global filter_partner_ids
        partner_obj = self.env['res.partner'].sudo()
        if not options:
            options = informations['options']
            filter_partner_ids = options.get('partners_to_show', [])
#         elif not set(informations['options'].get('partners_to_show', [])) & set(filter_partner_ids):
#             filter_partner_ids = informations['options'].get('partners_to_show', [])
        partners_ids = []
        if informations['options'].get('partners', []):
            partners_ids = [int(partner) for partner in informations['options'].get('partners', [])]
        if not set(partners_ids) & set(informations['options'].get('partners_to_show', [])):
            filter_partner_ids = informations['options'].get('partners_to_show', [])
        searchview_dict = {'options': options, 'context': self.env.context}
        partners = partner_obj.browse()
        for partner in filter_partner_ids:
            partners += partner_obj.browse(partner)
        searchview_dict['partners'] = [(p.id, p.name) for p in partners] or False
        informations['searchview_html'] = self.env['ir.ui.view'].render_template(self.get_templates().get('search_template', 'account_reports.followup_search_template'), values=searchview_dict)
        return informations


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_partners_in_need_of_action(self, overdue_only=False):
        result = super(ResPartner, self).get_partners_in_need_of_action(overdue_only)
        if self._context.get('partner_ids', []):
            return self.browse(self._context.get('partner_ids'))
        return result
