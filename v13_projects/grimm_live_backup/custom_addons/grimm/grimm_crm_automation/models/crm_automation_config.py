# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dipak Suthar
#    Copyright 2022 Grimm Gastronomiebedarf
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import base64

from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import NamedTemporaryFile
from datetime import date,datetime, timedelta
from odoo.exceptions import UserError
import os.path
import csv
import ast

_logger = logging.getLogger(__name__)

class CRMStage(models.Model):
    _inherit = 'crm.stage'

    delete_activities = fields.Boolean("Clear all activities")

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    last_state_update = fields.Datetime("Last State Updated")

    def _track_template(self, changes):
        res = super(CRMLead, self)._track_template(changes)
        if 'stage_id' in changes:
            for lead in self:
                lead.last_state_update = fields.Datetime.now()
                if lead.stage_id.delete_activities:
                    lead.mark_all_activities_done()
        return res

    def mark_all_activities_done(self):
        '''
        This method will mark all activity for those record as done.
        :return:
        '''
        exist_activity = self.env["mail.activity"].sudo().search([('res_model', '=', self._name),('res_id', '=', self.id)])
        for activity in exist_activity:
            activity.action_done()

    def action_set_won(self):
        res = super(CRMLead, self).action_set_won()
        self.mark_all_activities_done()
        return res

    def action_set_lost(self, **additional_values):
        res = super(CRMLead, self).action_set_lost(**additional_values)
        self.mark_all_activities_done()
        return res

class CRMAutomationConfigLine(models.Model):
    _name = "crm.automation.config.line"
    _description = 'CRM Automation Configuration Line'

    _order = "config_id, stage_sequence"

    config_id = fields.Many2one('crm.automation.config','Config Id')

    src_state = fields.Many2one('crm.stage', string='Origin State')
    stage_sequence = fields.Integer('Stage Sequence', related='src_state.sequence', store=True)
    move_day = fields.Integer(string='Move After')
    dest_state = fields.Many2one('crm.stage', string='Destination State')
    template_id = fields.Many2one('mail.template', string='Mail Template')
    is_advance_domain = fields.Boolean(string="Advance Filter for this rule?", help="With this option you can set your custom filter for the lead selection.")

    advance_domain = fields.Char(string='Domain', default=[])

    _sql_constraints = [
        ('state_unique', 'unique (src_state,config_id)',_('You can not assign same origin state twice.!')),
        ('both_state_unique', 'unique (src_state,dest_state)',_('You can not assign same Origin state and Destination state.!'))
    ]

class CRMAutomationConfig(models.Model):
    _name = "crm.automation.config"
    _description = 'CRM Automation Configuration'

    name = fields.Char('Config Name')
    lead_domain = fields.Char('Lead Domain')
    active = fields.Boolean('Active', default=True)
    config_lines = fields.One2many('crm.automation.config.line', 'config_id', string="Config Line")
    html_info = fields.Html("Information", readonly=True, compute="_get_html_info")

    def _get_html_info(self):
        self.html_info = ""
        for record in self:
            transit_message = _("After <b>%s</b> days lead will automatically move to <b>%s</b> state.")
            title_message = _("Graphical Presentation of Pipeline")
            html_info = "<div class='container grimm_container'><div class='wrapper grimm_wrapper'><center><h1 class='h1_crm_automation'>%s</h1></center>"%title_message
            for line in record.config_lines:
                html_info += "<ul class='grimm_sessions'>"
                html_info += "<li class='crm_automation'><div class='time'><b>%s</b></div><p class='grimm_p'>%s</p>%s</li>"%(line.src_state.name, transit_message%(line.move_day,line.dest_state.name),  "" if not line.template_id.name else "Mail - %s"%line.template_id.name)
                html_info += "<li class='crm_automation'><div class='time'><b>%s</b></div><p class='grimm_p'></p></li>" % (line.dest_state.name)
                html_info += "</ul>"
            html_info += "</div></div><br/>"

            record.html_info=html_info
    @api.model
    def create(self, vals):
        '''
        Inherited for add validation so there should be only one active configuration.
        :param vals:
        :return:
        '''
        existed_config = self.sudo().search_count([('active', '=', True)])
        if existed_config >= 1:
            raise UserError(_('Only one active configuration possible. Please de-activate other active configuration.'))
        return super(CRMAutomationConfig, self).create(vals)

    def write(self, vals):
        '''
        :param vals:
        :return:
        '''
        if isinstance(vals, dict):
            if 'active' in vals.keys() and vals.get("active", False):
                existed_config = self.sudo().search_count([('active', '=', True)])
                if existed_config >= 1:
                    raise UserError(_('Only one active configuration possible. Please de-activate other active configuration.'))
        return super(CRMAutomationConfig, self).write(vals)

    def _scheduler_automate_crm_pipeline(self):
        # Purchase price update code START
        try:
            self._cr.execute("UPDATE shopware6_product_update_queue SET is_done='f' WHERE product_id IN (SELECT id FROM product_product WHERE (special_purchase_price_to IS NOT NULL OR special_purchase_price_from IS NOT NULL) AND id IN (SELECT openerp_id FROM shopware6_product_product));")
        except Exception as e:
            _logger.warn(str(e))
        # purchase price code update STOP

        final_string = ""
        active_config = self.sudo().search([('active', '=', True)], limit=1)

        current_time = fields.Datetime.now()
        for config_line in active_config.config_lines:
            lead_domain = ast.literal_eval(active_config.lead_domain) if active_config.lead_domain else []
            if config_line.src_state.id != config_line.dest_state.id:
                new_date = current_time - timedelta(days=config_line.move_day)
                compare_date = "last_state_update" #"last_state_update"
                final_string += "Check lead last update less than ==> %s" % new_date
                need_to_update = self.env["crm.lead"].sudo().search([('type','=','opportunity'),('stage_id', '=', config_line.src_state.id),(compare_date, '<=', new_date)])
                if lead_domain:
                    need_to_update = need_to_update.filtered_domain(lead_domain)
                final_string += " found lead to update stage after filter domain ===> %s " % need_to_update
                if need_to_update:
                    need_to_update.write({'stage_id': config_line.dest_state.id})
                    post_message = _("Stage changed from <b>%s <span class='fa fa-long-arrow-right' role='img' aria-label='Changed' title='Changed'/> %s</b> by CRM pipe line automation. Config name <b>%s</b>")
                    for to_update in need_to_update:
                        to_update.message_post(body=post_message % (config_line.src_state.name, config_line.dest_state.name, active_config.name))
                        if config_line.template_id:
                            sale_id = self.env["sale.order"].sudo().search([('opportunity_id', '=', to_update.id)])
                            final_string += " will send mail from sale order ===> %s "% sale_id
                            for sale in sale_id:
                                config_line.template_id.sudo().send_mail(sale.id, force_send=True,notif_layout="mail.message_notification_email")
                        _logger.info("CRM lead %s state changed by automatic pipeline."%(to_update))
        return final_string

class SaleReminderLog(models.Model):
    _name = "sale.reminder.log"
    _description = 'Sale Reminder Log'

    res_id = fields.Integer("Res Id")
    res_model = fields.Char("Model")

    _sql_constraints = [
        ('res_id_res_model_uniq', 'unique(res_id,res_model)', 'Resource must be unique !'),
    ]

class SaleAutomationConfig(models.Model):
    _name = "sale.automation.config"
    _description = 'Sale Automation Configuration'

    name = fields.Char('Config Name')
    active = fields.Boolean('Active', default=True)
    older_than = fields.Integer("Older than (days)", required=1)
    activity_title = fields.Char('Activity Title')
    model_domain = fields.Char('Filter')
    activity_note = fields.Html('Activity Note')
    activity_summary = fields.Char('Activity Summary')
    activity_type = fields.Many2one('mail.activity.type', string='Activity Type')

    def _check_existing_open_activity(self, record, acivate_config):
        #exist_activity = self.env["mail.activity"].sudo().search([('res_model', '=', record._name),('res_id', '=', record.id),('activity_type_id', '=', acivate_config.activity_type.id)])
        exist_activity = self.env["sale.reminder.log"].sudo().search([('res_model', '=', record._name), ('res_id', '=', record.id)])
        if not exist_activity:
            try:
                new_activity_id = self.env["sale.reminder.log"].create({'res_model':record._name, 'res_id':record.id})
            except:
                pass
        return True if exist_activity else False

    def assign_activity(self, record, acivate_config):
        if not self._check_existing_open_activity(record, acivate_config):
            vals = {}
            vals["activity_type_id"] = acivate_config.activity_type.id
            dead_line = date.today()+ timedelta(days=1)
            if dead_line.isoweekday() == 6: # If Deadline is Saturday set to Monday (adding 2 days)
                dead_line = dead_line + timedelta(days=2)
            elif dead_line.isoweekday() == 7: # If Deadline is Sunday set to Monday (adding 1 days)
                dead_line = dead_line + timedelta(days=1)
            # vals["date_deadline"] = dead_line
            # vals["summary"] = acivate_config.activity_summary
            # vals["note"] = acivate_config.activity_note
            # vals["res_name"] = record.name
            # vals["res_model"] = record._name
            # vals["res_id"] = record.id
            # model_id = self.env['ir.model'].sudo().search([('model', '=', record._name)], limit=1)
            # if model_id:
            #     vals["res_model_id"] = model_id.id
            # vals["user_id"] = record.user_id.id
            # new_activity_id = self.env['mail.activity'].create(vals)
            record.activity_schedule(
                acivate_config.activity_type.get_external_id().get(acivate_config.activity_type.id), dead_line,
                record.name,
                user_id=record.user_id.id)

    def _scheduler_automate_sale_pipeline(self):
        active_config = self.sudo().search([('active', '=', True)], limit=1)
        if active_config:
            domain = ast.literal_eval(active_config.model_domain)
            past_date = fields.Datetime.now() - timedelta(days=active_config.older_than)
            sale_order = self.env["sale.order"].sudo().search([]).filtered_domain(domain)
            subtype_note_id = self.env.ref('mail.mt_note').id
            subtype_discussion_id = self.env.ref('mail.mt_comment').id
            for order in sale_order:
                self._cr.execute("select create_date from mail_message where res_id=%s and model='%s' and subtype_id in (%s, %s) and message_type in ('comment','email') order by create_date desc limit 1" % (order.id, order._name, subtype_note_id, subtype_discussion_id))
                last_interaction_date = [x[0] for x in self._cr.fetchall()]
                if not last_interaction_date: # If there is no last interaction date then we use order create_date
                    last_interaction_date = [order.create_date]
                if last_interaction_date[0] < past_date:
                    _logger.info("%s ===========Last Message date====>>>> %s"%(order, str(last_interaction_date[0])))
                    self.assign_activity(order, active_config)