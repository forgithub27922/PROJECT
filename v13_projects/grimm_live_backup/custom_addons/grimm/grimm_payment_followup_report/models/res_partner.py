# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools.misc import format_date
from odoo.osv import expression
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountFollowupFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    template_id = fields.Many2one(comodel_name='mail.template',
                                              string='Mail Template',
                                              help="Odoo will send an email once invoice is in this level.")
    report_title = fields.Char(string="Report Title")
class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    grimm_followup_level_id = fields.Many2one(comodel_name='account_followup.followup.line', string='Grimm Followup Level', help="Highest Follow-up level for all invoices.", group_expand='_read_group_stage_ids', track_visibility='onchange')
    grimm_next_reminder = fields.Date("Grimm Next reminder.")
    payment_state_update = fields.Boolean("Is payment state updated?", store=True, compute="_compute_payment_state_updated")

    def get_mahnung_partner_id(self):
        '''
        This method return mahnung partner id and its language for mail template.
        :return: [str(partner_ids), language] Partner_ids will use for receipient and language for email language.
        '''
        mahnung_partner_id = ""
        for invoice in self:
            mahnung_partner_id = self.env['res.partner'].browse(invoice.partner_id.address_get(['invoice'])['invoice'])
            if invoice.partner_id.send_mahnung:
                mahnung_partner_id = invoice.partner_id
            elif invoice.partner_id.parent_id:
                for child in invoice.partner_id.parent_id.child_ids:
                    if child.send_mahnung:
                        mahnung_partner_id = child
                        break
        return [str(mahnung_partner_id.id),mahnung_partner_id.lang or "de_DE"]

    @api.depends("invoice_payment_state")
    def _compute_payment_state_updated(self):
        self.payment_state_update = False
        for invoice in self:
            if invoice.invoice_payment_state == "paid": # Extra code not related to mahnung partner id, just to set grimm payment follow-up
                invoice.grimm_followup_level_id = False


    def _track_template(self, changes):
        res = super(AccountMove, self)._track_template(changes)
        for invoice in self:
            if 'grimm_followup_level_id' in changes:
                if invoice.invoice_date_due and invoice.grimm_followup_level_id:
                    # invoice.grimm_next_reminder = invoice.invoice_date_due + timedelta(days=invoice.grimm_followup_level_id.delay)
                    total_dl = (fields.Date.today() - invoice.invoice_date_due).days # 1101
                    next_level = self.env['account_followup.followup.line'].search([('delay', '>', total_dl)],order="delay", limit=1)
                    if next_level:
                        invoice.grimm_next_reminder = fields.Date.today() + timedelta(days=next_level.delay - total_dl)
                    else:
                        next_level = self.env['account_followup.followup.line'].search([('delay', '>', invoice.grimm_followup_level_id.delay)],order="delay", limit=1)
                        diff = invoice.grimm_followup_level_id.delay
                        if next_level:
                            diff = next_level.delay - diff
                        invoice.grimm_next_reminder = (fields.Date.today()) + timedelta(days=diff)
                    if self._context.get("send_mail_to_customer", False) and invoice.grimm_followup_level_id.template_id:
                        invoice.grimm_followup_level_id.template_id.sudo().send_mail(invoice.id)
        return res

    def call_grimm_payment_reminder(self):
        invoices = self.search([('payment_mode_id','in', [4,27]),('grimm_followup_level_id','=', False),('invoice_payment_state','=', 'not_paid'),('type','=', 'out_invoice'),('state','=', 'posted'), ('grimm_next_reminder','=', False), ('invoice_date_due','<', fields.Date.today())])
        first_followup_level = self.env['account_followup.followup.line'].search([], order="delay asc", limit=1)
        last_followup_level = self.env['account_followup.followup.line'].search([], order="delay desc", limit=1)

        for inv in invoices:
            # inv.grimm_next_reminder = inv.invoice_date_due  + timedelta(days=first_followup_level.delay)
            total_dl = (fields.Date.today() - inv.invoice_date_due).days
            temp_followup_level = self.env['account_followup.followup.line'].search([('delay', '<=', total_dl)], order="delay desc", limit=1)
            if temp_followup_level:
                inv.with_context(send_mail_to_customer=True).grimm_followup_level_id = temp_followup_level
        invoices = self.search([('payment_mode_id','in', [4,27]),('invoice_payment_state', '=', 'not_paid'), ('grimm_next_reminder','!=', False), ('grimm_next_reminder', '<=', fields.Date.today()), ('type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date_due','<', fields.Date.today())])
        for inv in invoices:
            total_delay = inv.grimm_followup_level_id.delay if inv.grimm_followup_level_id else 0 # If reminderlevel is not set it will get the first level due to Zero
            next_followup = self.env['account_followup.followup.line'].search([('delay', '>', total_delay),('company_id', '=', inv.company_id.id)],order="delay asc", limit=1)
            if next_followup:
                inv.with_context(send_mail_to_customer=True).grimm_followup_level_id = next_followup
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        search_domain = [('id', '>', 0)]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    send_mahnung = fields.Boolean("Send Mahnung", default=False)
    grimm_followup_level_id = fields.Many2one(comodel_name='account_followup.followup.line', string='Grimm Followup Level', help="Highest Follow-up level for all invoices.", compute="_get_highest_followup_level")

    override_followup_level = fields.Many2one(comodel_name='account_followup.followup.line',
                                 string='Override Followup Level',
                                 help="Tatsächlich wird die Folgeebene dadurch nicht überschrieben. Wir verwenden dieses Feld, um den Ebenentitel nur für den Druck von Briefen zu drucken.")

    def _get_highest_followup_level(self):
        self.grimm_followup_level_id = False
        for partner in self:
            invoices = partner.invoice_ids.filtered(lambda r: r.invoice_payment_state == 'not_paid' and r.invoice_date_due and r.invoice_date_due > fields.Date.today() and r.grimm_followup_level_id != False)
            if invoices:
                partner.grimm_followup_level_id = self.env['account_followup.followup.line'].sudo().search([('id', 'in', invoices.mapped("grimm_followup_level_id.id"))], order="delay desc",limit=1)

    def _execute_followup_partner(self):
        self.ensure_one()
        if self.followup_status == 'in_need_of_action':
            followup_line = self.followup_level
            if followup_line.send_email:
                self.send_followup_email()
            if followup_line.manual_action:
                # log a next activity for today
                activity_data = {
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'activity_type_id': followup_line.manual_action_type_id.id or self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': followup_line.manual_action_note,
                    'user_id': followup_line.manual_action_responsible_id.id or self.env.user.id,
                }
                self.env['mail.activity'].create(activity_data)
            if followup_line:
                next_date = followup_line._get_next_date()
                self.update_next_action(options={'next_action_date': datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT), 'action': 'done'})
            if followup_line.print_letter:
                return self
        return None

    def execute_followup(self):
        """
        Execute the actions to do with followups.
        """
        to_print = self.env['res.partner']
        for partner in self:
            partner_tmp = partner._execute_followup_partner()
            if partner_tmp:
                to_print += partner_tmp
        if not to_print:
            return
        return self.env['account.followup.report'].print_followups(to_print)

    def _assign_followers_to_partner(self, res_id=False, partner_ids=[], model_name='res.partner'):
        if res_id:
            if not partner_ids:
                partner_ids = self.env['ir.config_parameter'].sudo().get_param('account.followup.followers', default="").split(",")
            sub_type_note = self.env.ref('mail.mt_note').id
            sub_type_comment = self.env.ref('mail.mt_comment').id
            sub_type_activities = self.env.ref('mail.mt_activities').id
            for partner in partner_ids:
                partner = int(partner)
                existing_follower = self.env['mail.followers'].search(
                    [('res_id', '=', res_id), ('res_model', '=', model_name), ('partner_id', '=', partner)], limit=1)
                if existing_follower:
                    existing_follower.subtype_ids = [(6, 0, [sub_type_note, sub_type_comment, sub_type_activities])]
                else:
                    self.env['mail.followers'].create({'res_id': res_id, 'res_model': model_name, 'partner_id': partner,
                                                       'subtype_ids': [
                                                           (6, 0, [sub_type_note, sub_type_comment, sub_type_activities])]})

    def _cron_execute_followup(self):
        followup_data = self._query_followup_level(all_partners=True)
        in_need_of_action = self.env['res.partner'].browse([d['partner_id'] for d in followup_data.values() if d['followup_status'] == 'in_need_of_action'])
        in_need_of_action_auto = in_need_of_action.filtered(lambda p: p.followup_level.auto_execute)
        #in_need_of_action_auto = self.env['res.partner'].browse([12231])

        aged_filter = self.env['partner.aged.filter'].search([], limit=1)
        move_ids = []
        if aged_filter:
            import ast
            domain = ast.literal_eval(aged_filter.name)
            if domain:
                move_ids = self.env['account.move'].sudo().search(domain).ids

        manual_letters = []

        for partner in in_need_of_action_auto:
            try:
                received_lines = self.env["account.followup.report"].get_follow_up_line(options={'partner_id': partner.id})
                ''' We are receiving all lines if net total is more than 0 we will receive level 3'''
                levels = [r_line.get("level",0) for r_line in received_lines]
                if 3 in levels:
                    partner._execute_followup_partner()
                    self._assign_followers_to_partner(res_id=partner.id, partner_ids=[])
            except UserError as e:
                # followup may raise exception due to configuration issues
                # i.e. partner missing email
                manual_letters.append(partner)
                _logger.exception(e)

        last_followup_level = self.env['account_followup.followup.line'].search([('company_id', '=', self.env.company.id)], order="delay desc", limit=1)
        in_need_of_action = self.env['res.partner'].browse([d['partner_id'] for d in followup_data.values() if d['followup_status'] in ['in_need_of_action','with_overdue_invoices'] and d['followup_level'] == last_followup_level.id])
        in_need_of_action_auto = in_need_of_action.filtered(lambda p: p.followup_level.auto_execute)


        table_str = ""
        if manual_letters:
            table_str = "<br/><br/><table width='80%' align='center'><tr><th align='left'>Need to send letter : Kunde list</th></tr>"
            for partner in manual_letters:
                table_str += "<tr><td align='left'><a href='%s'>%s</a></td></tr>" % (
                    self.env['gteg.invoice.import']._compute_rec_link(partner.id, partner._name),
                    partner.name)
            table_str += "</table>"

        if in_need_of_action_auto:
            table_str += "<br/><br/><table width='80%' align='center'><tr><th align='left'>Invoice #</th><th align='left'>Kunde</th></tr>"
            for partner in in_need_of_action_auto:
                partners_and_children = self.env['res.partner'].sudo().search([('id', 'child_of', partner.id)])
                partner_invoices = self.env['account.move']
                for rec in partners_and_children:
                    inv_rec = rec.invoice_ids.filtered(lambda rec: rec.type in ["out_invoice"] and rec.state in ['posted'] and rec.invoice_payment_state != 'paid' and rec.payment_mode_id.id in [4])
                    if inv_rec:
                        partner_invoices += inv_rec
                #partner_invoices = partner.invoice_ids.filtered(lambda rec: rec.type in ["out_invoice"] and rec.state in ['posted'] and rec.invoice_payment_state != 'paid' and rec.payment_mode_id.id in [4])
                for partner_invoice in partner_invoices:
                    table_str += "<tr><td align='left'><a href='%s'>%s</a></td><td align='left'>%s</td></tr>" % (
                        self.env['gteg.invoice.import']._compute_rec_link(partner_invoice.id, partner_invoice._name),partner_invoice.name, partner_invoice.partner_id.name)
            table_str += "</table>"


        # user_ids = [user for user in task.project_id.user_ids]
        # if task.project_id.user_id:
        #     user_ids.append(task.project_id.user_id)
        # user_ids = list(set(user_ids))
        if table_str:
            vals = {'email_from': 'office@grimm-gastrobedarf.de',
                    'email_to': self.env["ir.config_parameter"].sudo().get_param("partner.aged.emails", default="d.suthar@grimm-gastrobedarf.de"),
                    'body_html': "Sehr geehrter Manager,<br/>Hier finden Sie eine Liste aller überfälligen Rechnungen. <br/>%s<br/>Danke." % (table_str),
                    'type': 'email',
                    'subject': 'Total Due list'}
            mail = self.env['mail.mail'].create(vals)
            if last_followup_level and last_followup_level.send_email:
                mail.send()

