from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    total_ot_hourly = fields.Float(
        compute='_get_total_overtime',
        string="Total OT/Hourly", store=True)
    total_ot_monthly = fields.Float(
        compute='_get_total_overtime',
        string="Total OT/Monthly", store=True)

    @api.depends('date_from', 'date_to', 'employee_id')
    def _get_total_overtime(self):
        RVALine_obj = self.env['roster.vs.attendance.line']
        roster_line_obj = self.env['hr.roster.line']
        total_ot_monthly = 0
        weekday_rate = 0
        weekend_rate = 0

        for rec in self:
            weekday_rate = rec.employee_id.overtime_rate_weekday
            weekend_rate = rec.employee_id.overtime_rate_weekend
    
            if weekday_rate < 0 or weekend_rate < 0:
                weekday_rate = rec.employee_id.department_id.\
                    overtime_rate_weekday
                weekend_rate = rec.employee_id.department_id.\
                    overtime_rate_weekend
            if weekday_rate < 0 or weekend_rate < 0:
                weekday_rate = rec.employee_id.desg_grade_id.\
                    overtime_rate_weekday
                weekend_rate = rec.employee_id.desg_grade_id.\
                    overtime_rate_weekend
            if weekday_rate < 0 or weekend_rate < 0:
                weekday_rate = rec.employee_id.company_id.overtime_rate_weekday
                weekend_rate = rec.employee_id.company_id.overtime_rate_weekend
            if weekday_rate < 0 or weekend_rate < 0:
                raise UserError("Please set overtime rate in company.")
            if rec.employee_id and rec.date_from and rec.date_to:
                week_day_ot_amount = 0
                weekend_ot_amount = 0
                start_date = rec.date_from
                end_date = rec.date_to
                temp_date = datetime.strptime(
                    start_date, DEFAULT_SERVER_DATE_FORMAT)
                while temp_date.strftime(
                    DEFAULT_SERVER_DATE_FORMAT) <= end_date:
                    line = RVALine_obj.search([
                        ('att_date', '>=', datetime.strftime(
                            temp_date, '%Y-%m-%d %H:%M:%S')),
                        ('att_date', '<=', datetime.strftime(
                            temp_date, '%Y-%m-%d 23:59:59')),
                        ('employee_id', '=', rec.employee_id.id),
                        ('attendance_id.state', '=', 'submit')], limit=1)
                    if line.actual_overtime > 0:
                        roster_line = roster_line_obj.search([
                            ('schedule_date', '>=', datetime.strftime(
                                temp_date, '%Y-%m-%d %H:%M:%S')),
                            ('schedule_date', '<=', datetime.strftime(
                                temp_date, '%Y-%m-%d 23:59:59')),
                            ('employee_id', '=', rec.employee_id.id),
                            ('roster_id.state', '=', 'confirm'),
                            ('holiday_type', 'in', ['weekoff', 'holiday'])],
                            limit=1)
    
                        if roster_line:
                            weekend_ot_amount += line.\
                                actual_overtime * weekend_rate
                        else:
                            week_day_ot_amount += line.\
                                actual_overtime * weekday_rate
    
                        total_ot_monthly += line.actual_overtime * weekday_rate
                    temp_date = temp_date + relativedelta.relativedelta(days=1)
                if rec.employee_id.ot_calculation_type == 'hourly':
                    rec.total_ot_hourly = weekend_ot_amount + week_day_ot_amount
                if rec.employee_id.ot_calculation_type == 'monthly':
                    rec.total_ot_monthly = total_ot_monthly