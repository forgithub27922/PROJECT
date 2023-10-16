# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Holidays(models.Model):
    _inherit = "hr.holidays"

    compoff_id = fields.Many2one('hr.compoff', 'Comp-Off')
    compoff_date_expired = fields.Date('Valid Till', readonly=True, copy=False)

    @api.constrains('date_from')
    def change_leave_date_from(self):
        today_date = datetime.today().date()
        for rec in self:
            holiday_type_rec = rec.holiday_status_id or False
            if rec.type == 'remove' and holiday_type_rec \
                    and holiday_type_rec.allow_advance \
                    and holiday_type_rec.hours_before > 0:
                from_date = datetime.strptime(
                    rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
                if today_date > from_date:
                    msg = "Date from must be grater or equal to today."
                    raise ValidationError(msg)

                leave_type_hours = holiday_type_rec.hours_before
                diff_days_hours = ((from_date - today_date).days) * 24
                if diff_days_hours < leave_type_hours:
                    error_msg = 'For ' + rec.holiday_status_id.name \
                                + ' you needs to apply before ' \
                                + str(leave_type_hours) + ' Hours.'
                    raise ValidationError(error_msg)

    @api.model
    def action_expired_compoff(self):
        """
        :return: Scheduler expired comp-off.
        """
        today_date = datetime.today().date()
        domain_allocate = [
            ('compoff_id', '!=', False),
            ('type', '=', 'add'),
            ('state', '=', 'validate'),
            ('compoff_date_expired', '<=', today_date),
            ('holiday_status_id.allow_compoff', '=', True)
        ]
        allocate_holiday_ids = self.search(domain_allocate,
                                           order='employee_id')
        for allocate_rec in allocate_holiday_ids:
            domain = [
                ('employee_id', '=', allocate_rec.employee_id.id),
                ('holiday_status_id', '=', allocate_rec.holiday_status_id.id),
                ('type', '=', 'remove'),
                ('state', '=', 'validate'),
                ('date_from', '>=', allocate_rec.date_from),
                ('date_to', '<=', today_date)]
            taken_compoff = self.search_count(domain)
            allocate_days = self.search_count(domain_allocate + [
                ('employee_id', '=', allocate_rec.employee_id.id)])

            if taken_compoff < allocate_days:
                lapse_days = allocate_days - taken_compoff
                self.lapse_remaining_leave(allocate_rec.compoff_date_expired,
                                           lapse_days,
                                           allocate_rec)

    @api.model
    def lapse_remaining_leave(self, expiry_date, lapse_days, compoff_rec):
        """
        :return: For create lapse comp-off.
        """
        name = 'Lapse Comp-Off'
        emp_rec = compoff_rec.employee_id or False
        leave_vals = {
            'name': name,
            'mode': 'employee',
            'holiday_status_id': compoff_rec.holiday_status_id.id,
            'employee_id': emp_rec and emp_rec.id or False,
            'date_from': expiry_date,
            'date_to': expiry_date,
            'number_of_days_temp': lapse_days,
            'department_id':
                emp_rec.department_id and emp_rec.department_id.id or False,
            'type': 'remove',
            'state': 'confirm',
        }
        lapse_compoff = self.create(leave_vals)
        lapse_compoff.action_approve()
        if lapse_compoff.holiday_status_id.double_validation:
            lapse_compoff.action_validate()
        return True

    # @api.constrains('holiday_status_id', 'date_from', 'date_to')
    # def check_leave_max_date(self):
    #     '''Override Limit: Not allow limit false after date end.'''
    #     for rec in self:
    #         if not rec.holiday_status_id.limit \
    #                 and rec.date_from and rec.date_to:
    #             allocate_holiday_ids = self.search([
    #                 ('employee_id', '=', rec.employee_id.id),
    #                 ('type', '=', 'add'),
    #                 ('state', '=', 'validate'),
    #                 ('holiday_status_id', '<=', rec.holiday_status_id.id),
    #             ], order='date_to desc', limit=1)
    #             last_date = ''
    #             if allocate_holiday_ids:
    #                 last_date = allocate_holiday_ids.date_to
    #                 if rec.holiday_status_id.allow_compoff:
    #                     last_date = allocate_holiday_ids.compoff_date_expired
    #             if last_date and rec.date_to > last_date:
    #                 wrn_msg = \
    #                     rec.holiday_status_id.name + \
    #                     ' date must be less than ' + str(last_date) + '.'
    #                 raise ValidationError(_(wrn_msg))


class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"

    allow_compoff = fields.Boolean(string='Comp-Off', help='Allow for comp-off.')
    expired_days = fields.Integer('Validity',
                                  help='Validity use for comp-off.')
    allow_advance = fields.Boolean('Allow in Advance',
                                   help="Allow to take in advance.")
    hours_before = fields.Integer('Advance',
                                  help='Take a leave in advance (Hours).')

    @api.onchange('allow_compoff', 'allow_advance')
    def onchange_compoff_advance(self):
        '''Onchange for "Allow to Compoff" & "Allow to Advance". '''
        if not self.allow_compoff:
            self.expired_days = 0
        if not self.allow_advance:
            self.hours_before = 0

    @api.constrains('allow_compoff', 'expired_days')
    def check_allow_compoff(self):
        '''Allow to Compoff: Not allow to set true in more than one leave type.
        '''
        old_leave_types = self.search([('allow_compoff','=', True),
                                       ('id','!=', self.id),
                                       ('company_id','=', self.company_id.id)])
        for rec in self:
            if rec.allow_compoff and old_leave_types:
                raise ValidationError(_('Comp-off type can not set more than one.'))
            if rec.allow_compoff and rec.expired_days <= 0:
                wrn_msg = 'Validity must be greater than zero.'
                raise ValidationError(_(wrn_msg))

    @api.constrains('allow_advance', 'hours_before')
    def check_hours_before(self):
        '''Allow to Advance: Set before hours greater than zero.'''
        for rec in self:
            if rec.allow_advance and rec.hours_before <= 0:
                wrn_msg = 'Advance hours must be greater than zero.'
                raise ValidationError(_(wrn_msg))
