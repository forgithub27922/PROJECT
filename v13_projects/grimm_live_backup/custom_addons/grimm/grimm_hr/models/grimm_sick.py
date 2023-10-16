#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
from odoo.exceptions import UserError
from datetime import date,datetime, timedelta
import logging
import urllib.request
import json
import requests
import json
_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    allow_entry = fields.Boolean("Allow Entry", default=True)


class LeaveReportCalendar(models.Model):
    _inherit = "hr.leave.report.calendar"

    holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type")

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_leave_report_calendar')

        self._cr.execute("""CREATE OR REPLACE VIEW hr_leave_report_calendar AS
        (SELECT 
            row_number() OVER() AS id,
            ce.name AS name,
            ce.start_datetime AS start_datetime,
            ce.stop_datetime AS stop_datetime,
            ce.event_tz AS tz,
            ce.duration AS duration,
            hl.employee_id AS employee_id,
            hl.holiday_status_id AS holiday_status_id,
            em.company_id AS company_id
        FROM hr_leave hl
            LEFT JOIN calendar_event ce
                ON ce.id = hl.meeting_id
            LEFT JOIN hr_employee em
                ON em.id = hl.employee_id
        WHERE 
            hl.state = 'validate');
        """)

class GrimmSick(models.Model):
    _name = "grimm.sick"
    _rec_name = 'emp_id'

    user_id = fields.Many2one('res.users', string="User")
    emp_id = fields.Many2one('hr.employee', string="Employee")
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type")
    data = fields.Binary('Datei', attachment=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.model
    def default_get(self, fields):
        result = super(GrimmSick, self).default_get(fields)
        result["user_id"] = self.env.user.id
        if self.env.user.employee_id:
            result["emp_id"] = self.env.user.employee_id.id
        result["leave_type_id"] = self.env.ref("hr_holidays.holiday_status_sl").id
        return result

    def _check_access(self):
        time_off_admin = self.env.ref("hr_holidays.group_hr_holidays_manager")
        return self.env.user.id in time_off_admin.users.ids

    def write(self, vals):
        if self._check_access():
            return super(GrimmSick, self).write(vals)
        dead_line = self.create_date + timedelta(days=3)
        if fields.Datetime.now()  > dead_line:
            raise UserError("You are not allowed to change request after 3 days.")
        return super(GrimmSick, self).write(vals)

class HolidaysRequest(models.Model):

    _inherit = "hr.leave"

    holiday_name = fields.Char("Holidays Name", readonly=True)
    sick_document = fields.Binary('Datei', attachment=True)
    sick_document_name = fields.Char('Datei Name')

    def _check_access(self):
        time_off_admin = self.env.ref("hr_holidays.group_hr_holidays_manager")
        return self.env.user.id in time_off_admin.users.ids

    def write(self, vals):
        for rec in self:
            if rec.holiday_status_id.id == 2:
                if rec._check_access():
                    continue
                dead_line = rec.create_date + timedelta(days=3)
                if fields.Datetime.now()  > dead_line:
                    raise UserError("You are not allowed to change request after 3 days for %s."%rec)
        return super(HolidaysRequest, self).write(vals)

    def _get_holiday_by_year(self, year):
        try:
            url = "https://feiertage-api.de/api/?jahr=%s&nur_land=BB" % year
            respons = urllib.request.urlopen(url)
            return json.loads(respons.read().decode(respons.info().get_param('charset') or 'utf-8'))
        except:
            return {}

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        print("Date changing ")
        if self.date_from and self.date_to:
            self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)['days']
            holiday_count = 0
            holiday_name = []
            self.holiday_name = ""
            for year in list(set([self.date_from.year, self.date_to.year])):
                holiday_data = self._get_holiday_by_year(year)
                for k, v in holiday_data.items():
                    holiday_date = datetime.strptime(v.get("datum"), '%Y-%m-%d').date()
                    week_day = holiday_date.weekday()
                    if week_day < 5 and (self.date_from.date() <= holiday_date <= self.date_to.date()):
                        holiday_count += 1
                        holiday_name.append("%s (%s)" % (k, holiday_date.strftime('%d.%m.%Y')))
            if holiday_name and self.number_of_days > 0:
                self.number_of_days -= holiday_count
                self.holiday_name = ", ".join(holiday_name)
        else:
            self.number_of_days = 0