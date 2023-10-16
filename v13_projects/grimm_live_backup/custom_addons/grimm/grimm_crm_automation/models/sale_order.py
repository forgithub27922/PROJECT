# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from itertools import groupby
from datetime import date,datetime, timedelta

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    lead_auto_create = fields.Boolean(string='Create Lead automatically', help="Lead will be automatically created aft creation of an offer.", default=True)
    is_lead_created_from_offer = fields.Boolean(string="Is lead created from offer?")
    followup_date = fields.Date(string="Nachverfolgungsdatum")

    def _default_lead_value(self, order):
        lead_vals = {}
        lead_vals["partner_id"] = order.partner_id.id
        lead_vals["user_id"] = order.user_id.id
        lead_vals["name"] = "%s %s "%(order.partner_id.name, order.order_subject or '')
        lead_vals["team_id"] = order.team_id.id
        lead_vals["planned_revenue"] = order.amount_untaxed
        lead_vals["type"] = 'opportunity'
        lead_vals["order_ids"] = [(4,order.id)]
        lead_vals["stage_id"] = self.env.ref("crm.stage_lead3").id
        return lead_vals

    def assign_activity(self, record, planned_date=False):
        vals = {}
        vals["activity_type_id"] = self.env.ref("note.mail_activity_data_reminder").id
        dead_line = planned_date
        if dead_line:
            vals["date_deadline"] = dead_line
        else:
            dead_line = date.today()+ timedelta(days=7)
            if dead_line.isoweekday() == 6: # If Deadline is Saturday set to Monday (adding 2 days)
                dead_line = dead_line + timedelta(days=2)
            elif dead_line.isoweekday() == 7: # If Deadline is Sunday set to Monday (adding 1 days)
                dead_line = dead_line + timedelta(days=1)
            vals["date_deadline"] = dead_line

        # vals["summary"] = "%s"%record.name
        # vals["note"] = "%s"%record.name
        # vals["res_name"] = record.name
        # vals["res_model"] = record._name
        # vals["res_id"] = record.id
        # model_id = self.env['ir.model'].sudo().search([('model', '=', record._name)], limit=1)
        # if model_id:
        #     vals["res_model_id"] = model_id.id
        # vals["user_id"] = record.user_id.id
        # print("We are going to create activity with =====> ", vals)
        record.activity_schedule(
                'note.mail_activity_data_reminder', dead_line,
                record.name,
                user_id=record.user_id.id)
        # new_activity_id = self.env['mail.activity'].create(vals)

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if result.lead_auto_create and not result.opportunity_id:
            if result.team_id and result.team_id.id in [1, 8]:
                lead_vals = self._default_lead_value(result)
                lead_id = self.env["crm.lead"].create(lead_vals)
                result.is_lead_created_from_offer = True
                self.assign_activity(lead_id, planned_date=result.followup_date)
        return result
