from odoo import models, fields, api
from datetime import date as dt
import calendar


class PublicHolidaysLine(models.Model):
    _inherit = 'hr.public.holidays.line'

    def process_tracking(self):
        """
        This method will look in to the tracking updates
        ------------------------------------------------
        @param self: object pointer
        """
        cr_dt = fields.Date.today()
        tracking_obj = self.env['time.tracking']
        emp_obj = self.env['hr.employee']
        for pub in self:
            pub_date = pub.date
            if pub_date.month == cr_dt.month:
                tracking = tracking_obj.search([('month', '=', str(pub_date.month)), ('year', '=', pub_date.year)])
                if tracking.ids:
                    # Update existing Tracking
                    emp_ids = tracking.mapped(lambda r: r.employee_id.id)
                    open_tracking = tracking.filtered(lambda r: r.state == 'open')
                    if open_tracking.ids:
                        open_tracking.generate_tracking()
                        open_tracking.compute_tracking()

                # Create New Tracking for missing ones
                emps = emp_obj.search([('id', 'not in', emp_ids)])
                if emps.ids:
                    month_range = calendar.monthrange(pub_date.year, pub_date.month)
                    st_dt = dt(pub_date.year, pub_date.month, 1)
                    en_dt = dt(pub_date.year, pub_date.month, month_range[1])
                    for emp in emps:
                        time_tracking = tracking_obj.create({
                            "name": "Time Tracking of " + emp.name + " - " +\
                                    str(pub_date.month) + '-' + str(pub_date.year),
                            "employee_id": emp.id,
                            'month': str(pub_date.month),
                            'year': pub_date.year,
                            "start_date": st_dt,
                            "end_date": en_dt,
                            "schedule_id": emp.resource_calendar_id.id})
                        time_tracking.generate_tracking()
                        time_tracking.compute_tracking()

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to update the tracking lines
        -----------------------------------------------------
        @param self: object pointer
        @param vals_lst: list of dictionaries containing fields and values
        :return: recordset of newly created record(s)
        """
        pubs = super(PublicHolidaysLine, self).create(vals_lst)
        pubs.process_tracking()
        return pubs

    def write(self, vals):
        """
        Overridden write method to update the tracking lines
        ----------------------------------------------------
        @param self: object pointer
        @param vals: dictionary containing fields and values
        :return: recordset of newly created record(s)
        """
        res = super(PublicHolidaysLine, self).write(vals)
        if vals.get('date', False):
            self.process_tracking()
        return res