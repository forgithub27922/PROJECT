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
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import UserError,ValidationError
import os.path
import csv
import ast

_logger = logging.getLogger(__name__)

class ContractType(models.Model):
    _name = "contract.type"

    name = fields.Char(string='Contract Type')

class ContractAdditionalDocument(models.Model):
    _name = "contract.additional.document"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Document Name')
    document = fields.Binary(string='Document', attachment=True)
    config_id = fields.Many2one('contract.config', 'Config Id')


class NotificationStage(models.Model):
    _name = "notification.stage"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    #user_id = fields.Many2one("res.users",string='User ID')
    user_ids = fields.Many2many("res.users", string="Users")
    sequence = fields.Integer(string='Sequence')
    #alarm_ids = fields.Many2many("calendar.alarm", string="Reminders")
    notice_date = fields.Date(string='Notice Date', related='config_id.notice_date')
    real_notice_date = fields.Date(string='Email send Date', compute='_get_real_notice_date', store=True)
    notify_before_days = fields.Integer(string='Day(s) prior to notice')
    config_id = fields.Many2one('contract.config', 'Config Id')
    is_mail_sent = fields.Boolean(string='Is Mail Sent?', default=False)

    @api.depends('notify_before_days')
    def _get_real_notice_date(self):
        self.real_notice_date = False
        for notif in self:
            notif.real_notice_date = notif.notice_date - relativedelta(days=notif.notify_before_days)

class ContractConfig(models.Model):
    _name = "contract.config"
    _description = 'Contract Configuration'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    _order = "contract_start_date"

    @api.model
    def select_uom(self):
        return [
            ('days', _('Days')),
            ('weeks', _('Weeks')),
            ('months', _('Months')),
            ('years', _('Years')),
        ]

    name = fields.Char(string='Contract Name')
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner','Partner', required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', track=True)
    contract_type_id = fields.Many2one('contract.type', 'Contract Type', track_visibility='onchange')
    number = fields.Char(string='Contract Number', track_visibility='onchange')
    document_name = fields.Char(string='Document Name')
    document = fields.Binary(string='Document', attachment=True)
    mimetype = fields.Char('Mimetype', compute='_compute_mimetype', store=True)
    object = fields.Char(string='Contract Object')
    comment = fields.Text(string='Comment', help="Here you can add note for this contract.")
    contract_start_date = fields.Date(string='Contract Start Date', track_visibility='onchange')
    contract_end_date = fields.Date(string='Contract End Date', track_visibility='onchange')
    notice_uom = fields.Selection(selection='select_uom', string='Notice in', required=True, default='months',
        help="Notice Period for termination.", track_visibility='onchange')
    notice = fields.Integer("Notice Period", track_visibility='onchange')
    notice_date = fields.Date(string='Notice Date', compute='_get_notice_date')

    auto_extend = fields.Boolean(string='Auto extend ?')

    extension_uom = fields.Selection(selection='select_uom', string='Extension in', required=True, default='months',
                                  help="Extend contract.", track_visibility='onchange')
    extension = fields.Integer("Extension", track_visibility='onchange')
    status = fields.Selection([('active','Active'),('check','Check'),('expired','Expired')], string='Status', help="Current Status of contract", compute='_get_current_status', store=True)

    notification_ids = fields.One2many("notification.stage","config_id", string="Notification")
    document_ids = fields.One2many("contract.additional.document", "config_id", string="Additional Docs")
    allow_cancel = fields.Boolean(string='Allow Cancel', compute='_get_allow_cancel')

    def _get_allow_cancel(self):
        self.allow_cancel = False
        for li in self:
            li.allow_cancel = True
            if li.notice_date:
                li.allow_cancel = True if li.notice_date > fields.date.today() else False

    @api.depends('document', 'document_name')
    def _compute_mimetype(self):
        """ compute the mimetype of the given values
            :return mime : string indicating the mimetype, or application/octet-stream by default
        """
        self.sudo().mimetype = ''
        for rec in self:
            if rec.document:
                rec.sudo().mimetype = guess_mimetype(base64.b64decode(rec.document))
            else:
                rec.sudo().mimetype = "application/pdf"

    def _get_notice_date(self):
        self.sudo().notice_date = False
        for contract in self.sudo():
            if contract.contract_end_date:
                if contract.notice_uom == "days":
                    contract.notice_date = contract.contract_end_date - relativedelta(days=contract.notice)
                elif contract.notice_uom == "weeks":
                    contract.notice_date = contract.contract_end_date - relativedelta(weeks=contract.notice)
                elif contract.notice_uom == "months":
                    contract.notice_date = contract.contract_end_date - relativedelta(months=contract.notice)
                elif contract.notice_uom == "years":
                    contract.notice_date = contract.contract_end_date - relativedelta(years=contract.notice)
        self._get_current_status()

    @api.onchange('contract_start_date','contract_end_date')
    def onchange_contract_date(self):
        if self.contract_start_date and self.contract_end_date:
            if self.contract_end_date < self.contract_start_date:
                raise ValidationError(_('Contract end date should be greater than start date.'))
            for notif in self.notification_ids:
                # Setting real notice date after changing contract start and end date.
                self.env["notification.stage"].browse(notif._origin.id).write({"real_notice_date": notif.notice_date - relativedelta(days=notif.notify_before_days)})
            self._get_notice_date()

    def _get_current_status(self):
        self.sudo().status = False
        for contract in self.sudo():
            if contract.contract_end_date and fields.Date.today() > contract.contract_end_date:
                contract.status = "expired"
            elif contract.contract_end_date and contract.notice_date < fields.Date.today() < contract.contract_end_date:
                contract.status = "check"
            elif (contract.contract_start_date) and contract.contract_start_date < fields.Date.today():
                contract.status = "active"

    def contract_cancel_request(self):
        self.ensure_one()
        template_id = self.env.ref('grimm_contract_mgt.email_template_contract_cancel_request', False)
        ctx = dict(
            default_model='contract.config',
            default_res_id=self.id,
            default_use_template=bool(template_id),
            default_template_id=template_id.id,
            default_composition_mode='comment'
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }
        return self.get_compose_message_dialogue('flavity_recruitment_extension.employee_email_template_ask_contract_question',employee)


    def contract_notify_email(self):
        current_date = fields.Date.today()

        # contract extension start
        contracts = self.sudo().search([('contract_end_date', '<', current_date), ('extension', '>', 0), ('auto_extend', '=', True)])
        for contract in contracts:
            if contract.extension_uom == "days":
                contract.contract_end_date = contract.contract_end_date + relativedelta(days=contract.extension)
            elif contract.extension_uom == "weeks":
                contract.contract_end_date = contract.contract_end_date + relativedelta(weeks=contract.extension)
            elif contract.extension_uom == "months":
                contract.contract_end_date = contract.contract_end_date + relativedelta(months=contract.extension)
            elif contract.notice_uom == "years":
                contract.contract_end_date = contract.contract_end_date + relativedelta(years=contract.extension)
            contract.message_post(
                body=_("<p>%s Contract has been auto extended to %s based on configuration.</p>" % (contract.name,contract.contract_end_date)),
                subject=_("Contract auto extention"), message_type='comment')
        # contract extension end

        template_id = self.env.ref('grimm_contract_mgt.email_template_notify_contract',False)
        if template_id:
            notifications = self.env["notification.stage"].sudo().search([('is_mail_sent', '=', False), ('real_notice_date', '<', current_date)])
            for notif in notifications.filtered(lambda r: r.config_id.status != 'expired'):
                template_id.sudo().send_mail(notif.config_id.id, force_send=True, notif_layout="mail.message_notification_email")
                notif.is_mail_sent = True