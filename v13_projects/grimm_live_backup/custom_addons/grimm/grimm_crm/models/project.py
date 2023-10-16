# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Hours
DEFAULT_MEETING_DURATION = 1
DEFAULT_MEETING_TYPE = 'Customer Meeting'


class ProjectTask(models.Model):
    _inherit = 'project.task'

    meeting_from = fields.Datetime(string='Start', copy=False,
                                   help='Meeting Start Datetime')
    meeting_to = fields.Datetime(string='End', copy=False,
                                 help='Meeting End Datetime')
    meeting_categ_id = fields.Many2one(comodel_name='calendar.event.type', string='Meeting Type',
                                       help='Once a task is created, Odoo will create a corresponding meeting of this type in the calendar.',
                                       default=lambda self: self._get_default_meeting_categ_id())
    meeting_id = fields.Many2one(comodel_name='calendar.event', string='Meeting', ondelete='cascade')

    @api.constrains('meeting_from', 'meeting_to')
    def _check_meeting_datetime(self):
        """
        Check, that start datetime lesser than end datetime
        """
        for record in self:
            if record.meeting_from and record.meeting_to:
                if record.meeting_from >= record.meeting_to:
                    raise ValidationError(
                        _("Ticket %s: Meeting: End Datetime must be greater than Start Datetime") % record.name)

    @api.model
    def _get_default_meeting_categ_id(self):
        """
        :return: get default meeting type
        :rtype: :class:`calendar.event.type <calendar.event.type>`
        """
        event_type = self.env['calendar.event.type'].search([('name', '=', DEFAULT_MEETING_TYPE)], limit=1)
        if event_type:
            return event_type

    @api.model
    def create(self, vals):
        """
        create calendar event after creating of task
        """
        res = super(ProjectTask, self).create(vals)
        if res.meeting_from and res.meeting_to:
            meeting_vals = res.prepare_meeting_vals()
            ctx_no_email = dict(self._context or {}, no_email=True)
            meeting_id = self.env['calendar.event'].with_context(no_email=True).create(meeting_vals)
            res.meeting_id = meeting_id
        return res

    def write(self, vals):
        """
        Update a existed or create new calendar event after changes
        """
        res = super(ProjectTask, self).write(vals)
        check_list = {'name': 'name', 'categ_ids': 'meeting_categ_id', 'user_id': 'user_id', 'start': 'meeting_from',
                      'stop': 'meeting_to'}
        is_meeting_chaged = [elemet for elemet in check_list if elemet in vals]
        ctx_no_email = dict(self._context or {}, no_email=True)
        for record in self:
            if record.meeting_from and record.meeting_to:
                if not record.meeting_id:
                    meeting_vals = record.prepare_meeting_vals()
                    meeting_id = self.env['calendar.event'].with_context(no_email=True).create(meeting_vals)
                    record.meeting_id = meeting_id
                elif is_meeting_chaged:
                    meeting_vals = record.prepare_meeting_vals()
                    """
                    parsed_meeting_vals = {}
                    for key, value in meeting_vals.iteritems():
                        if key in vals:
                            parsed_meeting_vals[key] = value
                    """
                    record.meeting_id.with_context(no_email=True).write(meeting_vals)

        return res

    @api.model
    def prepare_meeting_vals(self):
        """
        Prepare values for a calendar event from task
        :return: values in dict
        :rtype: dict
        """
        meeting_vals = {
            'name': _('Ticket %s') % self.name,
            'categ_ids': self.meeting_categ_id and [(6, 0, [self.meeting_categ_id.id])] or [],
            'user_id': self.user_id.id,
            'start': self.meeting_from,
            'stop': self.meeting_to,
            'allday': False,
            'state': 'open',  # to block that meeting date in the calendar
            'class': 'confidential',
        }
        # Add the partner_id (if exist) as an attendee
        attendee_ids = []
        """
        if self.user_id and self.user_id.partner_id:
            attendee_ids.append(self.user_id.partner_id.id)
            meeting_vals['user_id'] = self.user_id.id
        if self.claim_contact:
            attendee_ids.append(self.claim_contact.id)
            
        elif self.partner_id:
            attendee_ids.append(self.partner_id.id)
        """

        shipping_address = self.claim_shipping_id if self.claim_shipping_id else self.partner_id
        if shipping_address:
            shipping_address = "%s, %s %s" % (shipping_address.street, shipping_address.zip, shipping_address.city)
            meeting_vals['location'] = shipping_address

        try:
            # meeting_vals['description'] = html2text(self._description)
            soup = BeautifulSoup(self.description, 'lxml')
            meeting_vals['description'] = soup.get_text()
        except:
            meeting_vals['description'] = self.description

        meeting_vals['partner_ids'] = attendee_ids and [(6, 0, attendee_ids)] or []
        return meeting_vals
