# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, Warning
from .hijri import Convert_Date


class HrRoster(models.Model):
    _name = 'hr.roster'
    _inherit = 'mail.thread'

    name = fields.Char('Description')
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', ondelete="cascade",
        default=lambda self: self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1))
    start_date = fields.Date('Start Date')
    start_date_hijri = fields.Char('Start Date', size=10)
    end_date = fields.Date('End Date')
    end_date_hijri = fields.Char('End Date', size=10)
    roster_line_ids = fields.One2many('hr.roster.line', 'roster_id',
                                      'Roster Lines', ondelete="cascade")
    weekoff = fields.Many2many('weekoff.day', string='Weekoff Day')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('cancel', 'Cancelled')],
                             string='States',
                             track_visibility='always',
                             default='draft')
    is_exclude_break_time = fields.Boolean(string="Exclude Break Time",
                                           default=True,
                                           help="if true it will not count\
                                             break time in working hours")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.onchange('start_date', 'end_date', 'weekoff')
    def onchange_remove_line(self):
        self.roster_line_ids = False

    @api.multi
    @api.constrains('start_date', 'end_date', 'employee_id', 'state')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(
                        _('End Date must be greater than Start Date!'))
                if record.employee_id:
                    old_roster_recs = record.search([
                        ('employee_id', '=', record.employee_id.id),
                        ('state', '=', 'confirm'),
                        ('id', '!=', record.id)])
                    for old_roster_rec in old_roster_recs:
                        if old_roster_rec.start_date and \
                                old_roster_rec.end_date:
                            if old_roster_rec.start_date <= \
                                    record.start_date <= \
                                    old_roster_rec.end_date:
                                raise ValidationError(
                                    "You cannot overlap roster dates for same "
                                    "employee %s."%(old_roster_rec.employee_id.name))
                            if old_roster_rec.start_date <= \
                                    record.end_date <= \
                                    old_roster_rec.end_date:
                                raise ValidationError(
                                    "You cannot overlap roster dates for same "
                                    "employee %s."%(old_roster_rec.employee_id.name))

    @api.multi
    def state_confirm(self):
        """ Set roster state to Confirm. """
        for rec in self:
            if not rec.roster_line_ids:
                raise Warning(_("Please Generate Roster Lines."))
            rec.state = 'confirm'
            roster_vs_att_obj = self.env['roster.vs.attendance']
            vals = {
                'employee_id': rec.employee_id.id,
                'start_date': rec.start_date,
                'end_date': rec.end_date,
                'company_id': rec.company_id.id
            }
            roster_vs_att = roster_vs_att_obj.create(vals)
            roster_vs_att.generate_roster_attendance_lines()
            roster_vs_att.onchange_gregorian_date()
        return True

    @api.multi
    def cancel_roster(self):
        """ Set roster state to cancel """
        for rec in self:
            rost_vs_att_ids = self.env['roster.vs.attendance.line'].search(
                [('roster_line_id.roster_id', '=', rec.id)])
            if rost_vs_att_ids:
                raise ValidationError(
                    "You can not cancel Roster. \n Attendance entry\
                    already created for this Roster.")
            rec.state = 'cancel'

    @api.multi
    def action_set_to_draft(self):
        self.ensure_one()
        if not self.state == 'cancel':
            raise ValidationError(
                "You can only set to draft from Cancelled state.")
        self.state = 'draft'

    @api.onchange('start_date', 'end_date')
    def onchange_gregorian_date(self):
        """ Convert Gregorian date to Hijri """
        self.ensure_one()
        if self.start_date:
            self.start_date_hijri = Convert_Date(
                self.start_date, 'english', 'islamic')
        if self.end_date:
            self.end_date_hijri = Convert_Date(
                self.end_date, 'english', 'islamic')

    @api.onchange('start_date_hijri', 'end_date_hijri')
    def onchange_hijri_date(self):
        """ Convert Hijri date to Gregorian """
        self.ensure_one()
        if self.start_date_hijri:
            if self.start_date_hijri[4] != '-' or \
                    self.start_date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.start_date = Convert_Date(
                self.start_date_hijri, 'islamic', 'english')
        if self.end_date_hijri:
            if self.end_date_hijri[4] != '-' or \
                    self.end_date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.end_date = Convert_Date(
                self.end_date_hijri, 'islamic', 'english')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'confirm':
                raise Warning(_('You cannot delete confirmed Roster.'))
        return super(HrRoster, self).unlink()


class HrRosterLine(models.Model):
    _name = 'hr.roster.line'
    _order = 'schedule_date'

    @api.multi
    @api.depends('schedule_date')
    def _get_weekday(self):
        for roster_line in self:
            if roster_line.schedule_date:
                roster_line.week_day = datetime.strptime(
                    roster_line.schedule_date,
                    DEFAULT_SERVER_DATE_FORMAT).strftime('%A')

    roster_id = fields.Many2one('hr.roster', 'Roster', ondelete='cascade')
    shift_code_id = fields.Many2one(
        'hr.shift.code',
        'Shift Code',
        ondelete='restrict')
    holiday_type = fields.Selection([('holiday', 'Holiday'),
                                     ('weekoff', 'Week Off'),
                                     ('leave', 'Leave')],
                                    string="Holiday Type", )
    schedule_date = fields.Date('Date')
    week_day = fields.Char(compute="_get_weekday", string='Week Day')
    employee_id = fields.Many2one(related='roster_id.employee_id',
                                  relation='hr.employee',
                                  string='Employee', store=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
