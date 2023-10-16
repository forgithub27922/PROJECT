from odoo import models, fields
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta


class Employee(models.Model):
    _inherit = 'hr.employee'

    check_absent = fields.Boolean('Check Absent', compute='_check_emp_absent',
                                  search='_search_employee_attendance')
    description = fields.Char('Description', compute='_set_description')

    def _set_description(self):
        """
        This method is used to set the description in kanban view according to employee attendance
        ------------------------------------------------------------------------------------------
        :param self: object pointer
        """
        cr_dt = date.today()
        month_cal = calendar.monthrange(cr_dt.year, cr_dt.month)
        first_day = date(cr_dt.year, cr_dt.month, 1)
        last_day = date(cr_dt.year, cr_dt.month, month_cal[1])

        for emp in self:
            time_tracking = self.env['time.tracking'].search([('employee_id', '=', emp.id),
                                                              ('start_date', '=', first_day),
                                                              ('end_date', '=', last_day)], limit=1)
            desc = ''
            for line in time_tracking.tracking_line_ids:
                if line.date == cr_dt:
                    desc = line.name

            emp.description = desc

    def _check_emp_absent(self):
        """
        This method is used to check the employee is absent or not
        ----------------------------------------------------------
        :param self: object pointer
        """
        today_date = datetime.utcnow().date()
        today_start = fields.Datetime.to_string(today_date)
        today_end = fields.Datetime.to_string(today_date + relativedelta(hours=23, minutes=59, seconds=59))
        attendances = self.env['hr.attendance'].sudo().search([
            '|', ('employee_id', 'in', self.ids), ('check_out', '<=', today_end),
            ('check_in', '>=', today_start),
        ])
        emp_data = {}
        for att in attendances:
            for emp in att.employee_id:
                emp_data.update({emp.id: False})
                emp.check_absent = False

        for emp in self:
            if emp.id not in emp_data:
                emp.check_absent = True

    def _search_employee_attendance(self, operator, value):
        """
        This method is used to search the employee attendance for today
        ---------------------------------------------------------------
        :param self: object pointer
        """
        today_date = datetime.utcnow().date()
        today_start = fields.Datetime.to_string(today_date)
        today_end = fields.Datetime.to_string(today_date + relativedelta(hours=23, minutes=59, seconds=59))
        attendances = self.env['hr.attendance'].sudo().search([
            '|', ('employee_id', '!=', False), ('check_out', '<=', today_end),
            ('check_in', '>=', today_start)
        ])
        return [('id', 'not in', attendances.mapped('employee_id').ids)]
