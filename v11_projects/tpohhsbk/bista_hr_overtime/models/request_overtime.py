# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.bista_hr_roster.models.hijri import Convert_Date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

class RequestOvertime(models.Model):

    _name = 'request.overtime'
    _rec_name = 'employee_id'
    _inherit = 'mail.thread'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', ondelete="cascade",
        track_visibility='onchange', required=True)
    request_date = fields.Date(string="Overtime Date",
                               track_visibility='onchange', required=True)
    hijri_request_date = fields.Char(
        string="Hijri Request Date",
        track_visibility='onchange')
    request_duration = fields.Float(string="Request Duration",
                                    track_visibility='onchange', required=True)
    manager_id = fields.Many2one(
        related='employee_id.parent_id',
        string="Manager")
    calculated_duration = fields.Float(
        compute='_get_calculated_overtime_duration',
        string="Calculated Overtime", store=True)
    state = fields.Selection([
                            ('draft', 'Draft'),
                            ('confirm', 'Confirm'),
                            ('approve_manager', 'Approved by Manager'),
                            ('approve', 'Approved by HR'),
                            ('reject', 'Reject'),
                            ('cancel', 'Cancelled')
    ], string="State", default='draft', copy=False,
        track_visibility='onchange')
    comment = fields.Text(
        string="Comment",
        copy=False,
        track_visibility='onchange')
    rejection_reason = fields.Text(string="Reason For Rejection")
    is_manager = fields.Boolean(compute='_is_manager', string="Is Manager")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def _is_manager(self):
        for data in self:
            if self.env.user.id == data.manager_id.user_id.id:
                data.is_manager = True

    @api.constrains('request_date')
    def check_duplicate_ot_request(self):
        """prevent same date OT request"""
        today_date = datetime.strftime(datetime.now().date(), DF)
        if self.request_date > today_date:
            raise ValidationError("Future date overtime request not allowed.")
        n_records = self.env['request.overtime'].search_count(
            [('employee_id', '=', self.employee_id.id),
             ('request_date', '=', self.request_date), ('id', '!=', self.id),
             ('state', 'not in', ['cancel', 'reject'])])
        if n_records:
            raise ValidationError(
                "Overtime request for date %s already exist for\
                 this employee." % (self.request_date))

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
    @api.depends('request_date')
    def _get_calculated_overtime_duration(self):
        """ Get calculated OT from Roster vs Attendance"""
        for data in self:
            if data.request_date:
                att_line_id = self.env['roster.vs.attendance.line'].sudo().search(
                    [('employee_id', '=', data.employee_id.id),
                     ('att_date', '=', data.request_date)])
                if att_line_id:
                    att_line_id.attendance_id.\
                        generate_roster_attendance_lines()
                    att_line_id = self.env['roster.vs.attendance.line'].sudo().search(
                        [('employee_id', '=', data.employee_id.id),
                         ('att_date', '=', data.request_date)])
                    duration = att_line_id.overtime
                    data.calculated_duration = duration

    @api.multi
    def action_confirm(self):
        """Set state to confirm"""
        if not self.state == 'draft':
            raise ValidationError("You can only confirm from draft state.")
        self.state = 'confirm'

    @api.multi
    def action_approve_by_manager(self):
        if not self.state == 'confirm':
            raise ValidationError(
                "Approved by manager only allowed in 'Confirm' state.")
        self.state = 'approve_manager'

    @api.multi
    def action_cancel(self):
        """Set state to cancel"""
        self.state = 'cancel'

    @api.multi
    def action_reject(self):
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
            'context': {'overtime': True}
        }

    @api.multi
    def action_approve(self):
        """
        Generate entry in Roster vs Attendance and
        Set Request state to Approve
        """
        att_line_env = self.env['roster.vs.attendance.line']
        for rec in self:
            attr_line_id = att_line_env.search([
                ('att_date', '=', rec.request_date),
                ('employee_id', '=', rec.employee_id.id),
                ('att_date', '=', rec.request_date)], limit=1)
            if not attr_line_id:
                raise UserError("No roster vs attendance record found\
                for employee %s with date %s" % (
                    rec.employee_id.name, rec.request_date))
            attr_line_id.actual_overtime = rec.request_duration
            attr_line_id.overtime_request_id = rec.id
            rec.state = 'approve'
