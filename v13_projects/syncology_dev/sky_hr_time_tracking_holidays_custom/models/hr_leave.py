from odoo import models, fields
import calendar
from datetime import date as dt


class Leave(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        """
        Overridden method of leave and vacation approval to update the leave start and end time.
        It will also update the tracking line for the days
        ----------------------------------------------------------------------------------------
        @param self : object pointer
        """
        res = super(Leave, self).action_approve()
        tracking_line_obj = self.env['time.tracking.line'].sudo()
        for rec in self:
            flag = False
            tracking_lines = tracking_line_obj.search([('employee_id', '=', rec.employee_id.id),
                                                       ('date', '=', rec.request_date_from)], limit=1)
            if not tracking_lines:
                flag = True
                rec.process_tracking()
            if rec.leave_type == 'leave':
                tracking_lines = tracking_line_obj.search([('employee_id', '=', rec.employee_id.id),
                                                           ('date', '=', rec.request_date_from)], limit=1)
                tracking_lines.write({
                    'approved_leave_start_time': self.start_time,
                    'approved_leave_end_time': self. end_time,
                    'leave_id':self.id
                })
            elif rec.leave_type == 'vacation':
                tracking_lines = tracking_line_obj.search([('employee_id', '=', rec.employee_id.id),
                                                           ('date', '>=', rec.request_date_from),
                                                           ('date', '<=', rec.request_date_to)])
                tracking_lines.write({
                    'vacation_id': self.id
                })
            if not flag:
                tracking_lines.tracking_id.compute_tracking()
        return res

    def action_refuse(self):
        """
        Overridden method of leave and vacation refusal approval to update the tracking line for the days
        --------------------------------------------------------------------------------------------------
        @param self : object pointer
        """
        res = super(Leave, self).action_refuse()
        for rec in self:
            rec.process_tracking()
        return res

    def process_tracking(self):
        """
        This method will look in to the tracking updates
        ------------------------------------------------
        @param self: object pointer
        """
        cr_dt = fields.Date.today()
        tracking_obj = self.env['time.tracking'].sudo()
        emp_obj = self.env['hr.employee']
        emp_ids = []
        for leave in self:
            leave_start_date = leave.request_date_from
            if leave_start_date.month == cr_dt.month:
                tracking = tracking_obj.search([('month', '=', str(leave_start_date.month)), ('year', '=', leave_start_date.year)])
                if tracking.ids:
                    # Update existing Tracking
                    emp_ids = tracking.mapped(lambda r: r.employee_id.id)
                    draft_tracking = tracking.filtered(lambda r: r.state == 'draft')
                    in_progress_tracking = tracking.filtered(lambda r: r.state == 'in_progress')
                    if draft_tracking.ids:
                        draft_tracking.generate_tracking()
                        draft_tracking.compute_tracking()
                    if in_progress_tracking.ids:
                        in_progress_tracking.compute_tracking()
                # Create New Tracking for missing ones
                emps = emp_obj.search([('id', 'not in', emp_ids)])
                if emps.ids:
                    month_range = calendar.monthrange(leave_start_date.year, leave_start_date.month)
                    st_dt = dt(leave_start_date.year, leave_start_date.month, 1)
                    en_dt = dt(leave_start_date.year, leave_start_date.month, month_range[1])
                    for emp in emps:
                        time_tracking = tracking_obj.create({
                            "name": "Time Tracking of " + emp.name + " - " +\
                                    str(leave_start_date.month) + '-' + str(leave_start_date.year),
                            "employee_id": emp.id,
                            'month': str(leave_start_date.month),
                            'year': leave_start_date.year,
                            "start_date": st_dt,
                            "end_date": en_dt,
                            "schedule_id": emp.resource_calendar_id.id})
                        time_tracking.generate_tracking()
                        time_tracking.compute_tracking()
