# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.addons.bista_hr_roster.models.hijri import Convert_Date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime


class RequestException(models.Model):
    _name = 'request.exception'
    _description = "Exception Request"
    _rec_name = 'employee_id'
    _inherit = 'mail.thread'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', ondelete="cascade")
    action_type = fields.Selection([('update', 'Update Attendance'),
                                    ('add', 'Exception Hour')],
                                   string="Action", copy=False,
                                   default='update')
    type = fields.Selection([('forget_punch_in', 'Forget Punch In'),
                             ('forget_punch_out', 'Forget Punch Out')],
                             string='Reason')
    exception_type = fields.Selection([('field_work', 'Field Work'),
                            ('permission', 'Permission'),
                            ('other', 'Other Work')], string="Reason")
    reason = fields.Char(string='Reason')
    request_date = fields.Date(string='Request Date')
    hijri_request_date = fields.Char(string='Hijri Request Date')
    manager_approval_date = fields.Date(string='Approval Date')
    manager_approval_date_hijri = fields.Char(string='Approval Date',
                                              size=10)
    time_from = fields.Float(string='Time From')
    time_to = fields.Float(string='Time To')
    duration = fields.Float(string="Duration")
    comments = fields.Text('Comments', copy=False)
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('approve', 'Approve'), ('reject', 'Reject'),
                              ('cancel', 'Cancel')], string='States',
                             track_visibility='onchange', default='draft')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    cancel_reason = fields.Text(
        string="Cancellation Reason",
        track_visibility='onchange')

    @api.constrains('request_date')
    def check_duplicate_ot_request(self):
        today_date = datetime.strftime(datetime.now().date(), DF)
        if self.request_date > today_date:
            raise ValidationError("Future date overtime request not allowed.")
        """prevent same date OT request"""
        n_records = self.env['request.exception'].search_count(
            [('employee_id', '=', self.employee_id.id),
             ('request_date', '=', self.request_date), ('id', '!=', self.id),
             ('state', 'not in', ['cancel', 'reject']),('type','=',self.type),
             ('exception_type', '=', self.exception_type)])
        if n_records:
            raise ValidationError(
                "Exception request for date %s already exist\
                for this employee." % (self.request_date))

    @api.multi
    def action_set_to_draft(self):
        if not self.state == 'cancel':
            raise ValidationError("You can only set to draft from cancel.")
        self.state = 'draft'

    @api.onchange('action_type','exception_type', 'type')
    def onchange_type(self):
        if self.action_type =='add':
            self.reason = dict(self._fields['exception_type'].selection).get(
                self.exception_type)
        elif self.action_type =='update':
            self.reason = dict(self._fields['type'].selection).get(self.type)

    @api.onchange('request_date')
    def onchange_gregorian_date(self):
        """ Convert Gregorian date to Hijri """
        self.ensure_one()
        if self.request_date:
            self.hijri_request_date = Convert_Date(
                self.request_date, 'english', 'islamic')

    @api.onchange('hijri_request_date')
    def onchange_hijri_date(self):
        """ Convert Hijri date to Gregorian """
        self.ensure_one()
        try:
            if self.hijri_request_date:
                if self.hijri_request_date[4] != '-' or \
                        self.hijri_request_date[7] != '-':
                    raise ValidationError(
                        "Incorrect date format, should be YYYY-MM-DD")
                self.request_date = Convert_Date(
                    self.hijri_request_date, 'islamic', 'english')
        except ValueError:
            raise ValidationError("Incorrect date format,\
            should be YYYY-MM-DD")

    @api.multi
    def btn_confirm(self):
        """ Set Request state to confirm """
        for rec in self:
            rec.state = 'confirm'

    @api.multi
    def btn_approve(self):
        """ Set Request state to Approve """
        att_line_env = self.env['roster.vs.attendance.line']
        attendance_obj = self.env['hr.attendance']
        for rec in self:
            if rec.action_type == 'update':
                if rec.type == 'forget_punch_in':
                    if not rec.time_from:
                        raise UserError("Please enter 'Time From'.")

                    from_time = '{0:02.0f}:{1:02.0f}'.format(
                        *divmod(rec.time_from * 60, 60))
                    user_tz = self.env.user.tz
                    from_datetime = datetime.strptime(
                        rec.request_date, '%Y-%m-%d')
                    from_datetime = from_datetime.replace(
                        hour=int(from_time.split(':')[0]),
                        minute=int(from_time.split(':')[1]))
                    if not user_tz:
                        raise ValidationError(_('Please set timezone from \
                        preference.'))
                    else:
                        timezone = pytz.timezone(user_tz or pytz.utc)
                    from_datetime_aware = timezone.localize(from_datetime)
                    from_datetime_aware = from_datetime_aware.\
                        astimezone(pytz.utc)
                    from_datetime_str = datetime.strftime(
                        from_datetime_aware, DEFAULT_SERVER_DATETIME_FORMAT)
                    attendance_id = attendance_obj.search(
                        [
                            ('check_out', '>', from_datetime_str),
                            ('employee_id', '=', rec.employee_id.id),
                        ], limit=1)
                    if not attendance_id:
                        attendance_vals = {
                                'check_in': from_datetime_str,
                                'employee_id': rec.employee_id.id
                            }
                        attendance_obj.create(attendance_vals)
#                         raise UserError("Can not find attendance.")
                    else:
                        attendance_id.check_in = from_datetime_str
                    rec.manager_approval_date = fields.Date.context_today(self)

                if rec.type == 'forget_punch_out':
                    if not rec.time_to:
                        raise UserError("Please enter 'Time To'.")

                    time_to = '{0:02.0f}:{1:02.0f}'.format(
                        *divmod(rec.time_to * 60, 60))
                    user_tz = self.env.user.tz
                    if not user_tz:
                        raise ValidationError(_('Please set timezone from \
                        preference.'))
                    to_datetime = datetime.strptime(rec.request_date,
                                                    '%Y-%m-%d')
                    to_datetime = to_datetime.replace(hour=int(
                        time_to.split(':')[0]),
                        minute=int(time_to.split(':')[1]))

                    timezone = pytz.timezone(user_tz or pytz.utc)
                    to_datetime_aware = timezone.localize(to_datetime)
                    to_datetime_aware = to_datetime_aware.astimezone(pytz.utc)

                    to_datetime_str = datetime.strftime(
                        to_datetime_aware, DEFAULT_SERVER_DATETIME_FORMAT)

                    attendance_id = self.env['hr.attendance'].search(
                        [
                            ('check_in', '<', to_datetime_str),
                            ('employee_id', '=', rec.employee_id.id),
                        ], limit=1)

                    if not attendance_id:
                        raise UserError("Can not find attendance.")
                    attendance_id.check_out = to_datetime_str
                    rec.manager_approval_date = fields.Date.context_today(self)

            if rec.action_type == 'add':
                attr_line_id = att_line_env.search([
                    ('att_date', '=', rec.request_date),
                    ('employee_id', '=', rec.employee_id.id)], limit=1)
                if not attr_line_id:
                    raise UserError("No roster vs attendance record found\
                    for employee %s with date %s" % (
                        rec.employee_id.name, rec.request_date))
                attr_line_id.exception_hours = rec.duration
                attr_line_id.exception_request_id = rec.id
                rec.manager_approval_date = fields.Date.context_today(self)
        rec.state = 'approve'

    @api.multi
    def btn_reject(self):
        """ Set Request state to reject """
        view_id = self.env.ref(
            'bista_hr_roster.wiz_view_reject_req_exception_form')
        return {
            'name': 'Reject Ticket',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.reject.request.exception',
            'target': 'new',
        }

    @api.multi
    def btn_cancel(self):
        """ Set Request state to cancel """
        view_id = self.env.ref(
            'bista_hr_roster.wiz_view_cancel_form')
        return {
            'name': 'Cancellation Reason',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.cancel',
            'target': 'new',
        }
