import datetime
import math
from odoo import models, fields, api


class TimeTrackingLine(models.Model):
    _inherit = 'time.tracking.line'

    addition_ids = fields.One2many('hr.addition', 'tracking_line_id', 'Additions')
    penalty_ids = fields.One2many('hr.penalty', 'tracking_line_id', 'Penalties')

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to create penalties or additions
        ---------------------------------------------------------
        @param self: object pointer
        @param vals_lst: List of dictionaries containing fields and values.
        :return: recordset of newly created record(s)
        """
        penalty_obj = self.env['hr.penalty']
        # addition_obj = self.env['hr.addition']
        late_entry_penalty_type = self.env.company.late_entry_penalty_type_id
        early_exit_penalty_type = self.env.company.early_exit_penalty_type_id
        # overtime_addition_type = self.env.company.overtime_addtion_type_id
        time_tracking_line = super(TimeTrackingLine, self).create(vals_lst)
        previous_date = datetime.datetime.today() - datetime.timedelta(days=1)
        for vals in vals_lst:
            flag = False
            leave = time_tracking_line.leave
            # Find the Configured Worked Hours of Employee
            worked_hours = time_tracking_line.employee_id.count_working_hours(
                employee_id=time_tracking_line.employee_id,
                date=previous_date
            )

            if time_tracking_line.vacation:
                return time_tracking_line

            # if leave:
            #     hr_leaves = self.env['hr.leave'].search([('employee_id', '=', time_tracking_line.employee_id.id),
            #                                          ('request_date_from', '=', previous_date.date()),
            #                                          ('state', '=', 'validate'),
            #                                          ('leave_type', 'in', ('leave','vacation')),
            #                                          ('holiday_status_id.unpaid', '=', True)])
            #     for hr_leave in hr_leaves:
            #         worked_hours -= (hr_leave.end_time - hr_leave.start_time)
            if vals.get('actual_start_time', False) and time_tracking_line.diff_start_time:
                if leave:
                    en_time = time_tracking_line.approved_leave_end_time
                    if en_time >= time_tracking_line.actual_start_time:
                        flag = True
                if not flag:
                    penalty_vals = {
                        'employee_id': time_tracking_line.employee_id.id,
                        'date': time_tracking_line.date,
                        'penalty_type_id': late_entry_penalty_type.id,
                        'value_type': 'hours',
                        'value': time_tracking_line.diff_start_time,
                        'amount': time_tracking_line.employee_id.penalty_rate * time_tracking_line.employee_id.hourly_rate * late_entry_penalty_type.rate * time_tracking_line.diff_start_time,
                        'reason': 'Late Entry on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
                        'tracking_line_id': time_tracking_line.id,
                        'state': 'approved'
                    }

                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(time_tracking_line.diff_start_time)
                    late_by_time = time_tracking_line.diff_start_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        late_by_time = round(time_tracking_line.diff_start_time * 60)

                    # Find Penalties Entry as per the Late By Time
                    entries_values_late = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', late_by_time),
                        ('penalty_type_id', '=', late_entry_penalty_type.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_late:
                        value_type = False
                        amount = 0.0
                        value = entries_values_late.calculated_time
                        if entries_values_late.calculated_time_unit == 'days':
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * entries_values_late.calculated_time * worked_hours * time_tracking_line.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_late.calculated_time_unit == 'hours':
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * entries_values_late.calculated_time * time_tracking_line.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * (entries_values_late.calculated_time / 60) * time_tracking_line.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value

                        })
                    penalty_obj.create(penalty_vals)
            flag = False
            if vals.get('actual_end_time', False) and time_tracking_line.diff_end_time:
                if leave:
                    st_time = time_tracking_line.approved_leave_start_time
                    if st_time <= time_tracking_line.actual_end_time:
                        flag = True
                if not flag:
                    penalty_vals = {
                        'employee_id': time_tracking_line.employee_id.id,
                        'date': time_tracking_line.date,
                        'penalty_type_id': early_exit_penalty_type.id,
                        'value_type': 'hours',
                        'value': time_tracking_line.diff_end_time,
                        'amount': time_tracking_line.employee_id.penalty_rate * time_tracking_line.employee_id.hourly_rate * early_exit_penalty_type.rate * time_tracking_line.diff_end_time,
                        'reason': 'Early Exit on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
                        'tracking_line_id': time_tracking_line.id,
                        'state': 'approved'
                    }
                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(time_tracking_line.diff_end_time)
                    early_by_time = time_tracking_line.diff_end_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        early_by_time = round(time_tracking_line.diff_end_time * 60)

                    # Find Penalties Entry as per the Early By Time
                    entries_values_early = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', early_by_time),
                        ('penalty_type_id', '=', early_exit_penalty_type.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_early:
                        amount = 0.0
                        value_type = False
                        value = entries_values_early.calculated_time
                        if entries_values_early.calculated_time_unit == 'days':
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * entries_values_early.calculated_time * worked_hours * time_tracking_line.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_early.calculated_time_unit == 'hours':
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * entries_values_early.calculated_time * time_tracking_line.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * (entries_values_early.calculated_time / 60) * time_tracking_line.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value,
                        })
                    penalty_obj.create(penalty_vals)
            # if vals.get('actual_start_time', False) or vals.get('actual_end_time', False):
            #     if time_tracking_line.overtime_hours:
            #         addition_vals = {
            #             'employee_id': time_tracking_line.employee_id.id,
            #             'date': time_tracking_line.date,
            #             'addition_type_id': overtime_addition_type.id,
            #             'type_of_value': 'hours',
            #             'value': time_tracking_line.overtime_hours,
            #             'amount': time_tracking_line.employee_id.hourly_rate * time_tracking_line.overtime_hours,
            #             'reason': 'Overtime on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
            #             'tracking_line_id': time_tracking_line.id,
            #         }
            #         addition_obj.create(addition_vals)
        return time_tracking_line

    def write(self, vals):
        """
        Overridden write method to create penalties or additions
        --------------------------------------------------------
        @param self: object pointer
        @param vals: Dictionaru containing fields and values.
        :return: True
        """
        penalty_obj = self.env['hr.penalty']
        # addition_obj = self.env['hr.addition']
        late_entry_penalty_type = self.env.company.late_entry_penalty_type_id
        early_exit_penalty_type = self.env.company.early_exit_penalty_type_id
        absent_penalty_type = self.env.company.absence_penalty_type_id
        overtime_addition_type = self.env.company.overtime_addtion_type_id
        res = super(TimeTrackingLine, self).write(vals)
        previous_date = datetime.datetime.today() - datetime.timedelta(days=1)
        for time_tracking_line in self:
            flag = False
            leave = time_tracking_line.leave
            worked_hours = time_tracking_line.employee_id.count_working_hours(
                employee_id=time_tracking_line.employee_id,
                date=previous_date
            )

            if time_tracking_line.overtime_hours > 0.0:
                for add in time_tracking_line.addition_ids:
                    if overtime_addition_type == add.addition_type_id:
                        add.actual_overtime_hours = time_tracking_line.overtime_hours

            # if leave:
            #     hr_leaves = self.env['hr.leave'].search([('employee_id', '=', time_tracking_line.employee_id.id),
            #                                          ('request_date_from', '=', previous_date.date()),
            #                                          ('state', '=', 'validate'),
            #                                          ('leave_type', 'in', ('leave','vacation')),
            #                                          ('holiday_status_id.unpaid', '=', True)])

            #     for hr_leave in hr_leaves:
            #         worked_hours -= (hr_leave.end_time - hr_leave.start_time)

            if time_tracking_line.vacation:
                for penalty_id in time_tracking_line.penalty_ids:
                    penalty_id.unlink()
                return res

            if (vals.get('actual_start_time', False) or time_tracking_line.actual_start_time) and time_tracking_line.diff_start_time:
                penalty_hours = time_tracking_line.diff_start_time
                penalty = time_tracking_line.penalty_ids.filtered(
                        lambda r: r.penalty_type_id == late_entry_penalty_type)
                if leave and not (time_tracking_line.approved_leave_start_time > time_tracking_line.actual_start_time and time_tracking_line.approved_leave_end_time < time_tracking_line.actual_end_time):
                    en_time = time_tracking_line.approved_leave_end_time
                    penalty_hours = abs(en_time - time_tracking_line.actual_start_time) if not time_tracking_line.approved_leave_start_time > time_tracking_line.actual_start_time else penalty_hours
                    if en_time >= time_tracking_line.actual_start_time and not time_tracking_line.approved_leave_start_time > time_tracking_line.actual_start_time:
                        flag = True
                if not flag and time_tracking_line.actual_start_time and time_tracking_line.actual_end_time:
                    penalty_vals = {
                        'employee_id': time_tracking_line.employee_id.id,
                        'date': time_tracking_line.date,
                        'penalty_type_id': late_entry_penalty_type.id,
                        'value_type': 'hours',
                        'value': penalty_hours,
                        'amount': time_tracking_line.employee_id.penalty_rate * time_tracking_line.employee_id.hourly_rate * late_entry_penalty_type.rate * penalty_hours,
                        'reason': 'Late Entry on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
                        'tracking_line_id': time_tracking_line.id,
                        'state': 'approved'
                    }

                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(time_tracking_line.diff_start_time)
                    late_by_time = time_tracking_line.diff_start_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        late_by_time = round(time_tracking_line.diff_start_time * 60)

                    # Find Penalties Entry as per the Late By Time
                    entries_values_late = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', late_by_time),
                        ('penalty_type_id', '=', late_entry_penalty_type.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_late:
                        amount = 0.0
                        value_type = False
                        value = entries_values_late.calculated_time
                        if entries_values_late.calculated_time_unit == 'days':
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * entries_values_late.calculated_time * worked_hours * time_tracking_line.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_late.calculated_time_unit == 'hours':
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * entries_values_late.calculated_time * time_tracking_line.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = time_tracking_line.employee_id.penalty_rate * late_entry_penalty_type.rate * (entries_values_late.calculated_time / 60) * time_tracking_line.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value,
                        })
                    
                    if penalty:
                        penalty.write(penalty_vals)
                    else:
                        penalty_obj.create(penalty_vals)
                else:
                    if penalty:
                        penalty.unlink()
            flag = False
            if (vals.get('actual_end_time', False) or time_tracking_line.actual_end_time) and time_tracking_line.diff_end_time:
                penalty_hours = time_tracking_line.diff_end_time
                penalty = time_tracking_line.penalty_ids.filtered(
                        lambda r: r.penalty_type_id == early_exit_penalty_type)
                if leave and not (time_tracking_line.approved_leave_start_time > time_tracking_line.actual_start_time and time_tracking_line.approved_leave_end_time < time_tracking_line.actual_end_time):
                    st_time = time_tracking_line.approved_leave_start_time
                    penalty_hours = abs(time_tracking_line.actual_end_time - st_time) if st_time > time_tracking_line.actual_start_time else penalty_hours
                    if st_time <= time_tracking_line.actual_end_time and st_time > time_tracking_line.actual_start_time:
                        flag = True
                if not flag and time_tracking_line.actual_start_time and time_tracking_line.actual_end_time:
                    penalty_vals = {
                        'employee_id': time_tracking_line.employee_id.id,
                        'date': time_tracking_line.date,
                        'penalty_type_id': early_exit_penalty_type.id,
                        'value_type': 'hours',
                        'value': penalty_hours,
                        'amount': time_tracking_line.employee_id.penalty_rate * time_tracking_line.employee_id.hourly_rate * early_exit_penalty_type.rate * penalty_hours,
                        'reason': 'Early Exit on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
                        'tracking_line_id': time_tracking_line.id,
                        'state': 'approved'
                    }

                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(time_tracking_line.diff_end_time)
                    early_by_time = time_tracking_line.diff_end_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        early_by_time = round(time_tracking_line.diff_end_time * 60)

                    # Find Penalties Entry as per the Early By Time
                    entries_values_early = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', early_by_time),
                        ('penalty_type_id', '=', early_exit_penalty_type.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_early:
                        amount = 0.0
                        value_type = False
                        value = entries_values_early.calculated_time
                        if entries_values_early.calculated_time_unit == 'days':
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * entries_values_early.calculated_time * worked_hours * time_tracking_line.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_early.calculated_time_unit == 'hours':
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * entries_values_early.calculated_time * time_tracking_line.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = time_tracking_line.employee_id.penalty_rate * early_exit_penalty_type.rate * (entries_values_early.calculated_time / 60) * time_tracking_line.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value,
                        })

                    if penalty:
                        penalty.write(penalty_vals)
                    else:
                        penalty_obj.create(penalty_vals)
                else:
                    if penalty:
                        penalty.unlink()

            if (vals.get('actual_end_time', False) and time_tracking_line.actual_start_time) or (vals.get('actual_start_time', False) and time_tracking_line.actual_end_time):
                penalty = time_tracking_line.penalty_ids.filtered(
                        lambda r: r.penalty_type_id == absent_penalty_type)
                if penalty:
                    penalty.unlink()

            # if vals.get('actual_start_time', False) or vals.get('actual_end_time', False):
            #     if time_tracking_line.overtime_hours:
            #         addition_vals = {
            #             'employee_id': time_tracking_line.employee_id.id,
            #             'date': time_tracking_line.date,
            #             'addition_type_id': overtime_addition_type.id,
            #             'type_of_value': 'hours',
            #             'value': time_tracking_line.overtime_hours,
            #             'amount': time_tracking_line.employee_id.hourly_rate * time_tracking_line.overtime_hours,
            #             'reason': 'Overtime on ' + time_tracking_line.date.strftime('%Y-%m-%d'),
            #             'tracking_line_id': time_tracking_line.id,
            #         }
            #         addition = time_tracking_line.addition_ids.filtered(
            #             lambda r: r.addition_type_id == overtime_addition_type)
            #         if addition:
            #             addition.write(addition_vals)
            #         else:
            #             addition_obj.create(addition_vals)
        return res

    class TimeTracking(models.Model):
        _inherit = 'time.tracking'

        @api.model
        def _check_time_tracking(self):
            """
            This method will check time tracking every month for all the employees of the company and create
            penalty if they are absent.
            ------------------------------------------------------------------------------------------------
            @param self: object pointer
            """
            previous_date = datetime.datetime.today() - datetime.timedelta(days=1)
            tracking_lines = self.env['time.tracking.line'].search([
                ('pub_holiday', '=', False),
                ('week_off', '=', False),
                ('present', '=', False),
                ('date', '=', previous_date)
            ])

            penalty_obj = self.env['hr.penalty']
            abs_pn = self.env.company.absence_penalty_type_id
            lat_pn = self.env.company.late_entry_penalty_type_id
            early_pn = self.env.company.early_exit_penalty_type_id

            for track_ln in tracking_lines:
                worked_hours = track_ln.employee_id.count_working_hours(employee_id=track_ln.employee_id,
                                                                        date=previous_date)

                # if track_ln.leave:
                #     leave = self.env['hr.leave'].search([('employee_id', '=', track_ln.employee_id.id),
                #                                          ('request_date_from', '=', previous_date.date()),
                #                                          ('state', 'in', ('validate', 'validate1')),
                #                                          ('leave_type', 'in', ('leave','vacation')),
                #                                          ('holiday_status_id.unpaid', '=', True)])
                #     worked_hours -= (leave.end_time - leave.start_time)


                if abs_pn:
                    penalty_obj.create({
                        'employee_id': track_ln.employee_id.id,
                        'penalty_type_id': abs_pn.id,
                        'value_type': 'days',
                        'date': previous_date,
                        'issued_by': self.env.context.get('uid'),
                        'value': 1.0,
                        'tracking_line_id': track_ln.id,
                        'amount': track_ln.employee_id.penalty_rate * abs_pn.rate * 1.0 * track_ln.employee_id.hourly_rate * worked_hours,
                        'reason': 'Absent',
                        'state': 'approved'
                    })

                if lat_pn.penalty_entries:
                    penalty_vals = {
                    'employee_id': track_ln.employee_id.id,
                    'date': track_ln.date,
                    'value_type': 'hours',
                    'value': track_ln.diff_start_time,
                    'amount': track_ln.employee_id.penalty_rate * lat_pn.rate * track_ln.diff_start_time * track_ln.employee_id.hourly_rate,
                    'tracking_line_id': track_ln.id,
                    'issued_by': self.env.context.get('uid'),
                    'state': 'approved'
                    }

                    penalty_vals.update({
                        'penalty_type_id': lat_pn.id,
                        'reason': 'Late By'
                    })
                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(track_ln.diff_start_time)
                    late_by_time = track_ln.diff_start_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        late_by_time = round(track_ln.diff_start_time * 60)

                    # Find Penalties Entry as per the Late By Time
                    entries_values_late = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', late_by_time),
                        ('penalty_type_id', '=', lat_pn.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_late:
                        value = entries_values_late.calculated_time
                        amount = 0.0
                        value_type = False
                        if entries_values_late.calculated_time_unit == 'days':
                            amount = track_ln.employee_id.penalty_rate * lat_pn.rate * entries_values_late.calculated_time * worked_hours * track_ln.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_late.calculated_time_unit == 'hours':
                            amount = track_ln.employee_id.penalty_rate * lat_pn.rate * entries_values_late.calculated_time * track_ln.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = track_ln.employee_id.penalty_rate * lat_pn.rate * (entries_values_late.calculated_time / 60) * track_ln.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value,
                        })
                        penalty_obj.create(penalty_vals)

                if early_pn.penalty_entries:
                    penalty_vals = {
                    'employee_id': track_ln.employee_id.id,
                    'date': track_ln.date,
                    'value_type': 'hours',
                    'value': track_ln.diff_end_time,
                    'amount': track_ln.employee_id.penalty_rate * early_pn.rate * track_ln.diff_end_time * track_ln.employee_id.hourly_rate,
                    'tracking_line_id': track_ln.id,
                    'issued_by': self.env.context.get('uid'),
                    'state': 'approved'
                    }
                    penalty_vals.update({
                        'penalty_type_id': early_pn.id,
                        'reason': 'Early By'
                    })
                    # Convert late by time to minutes or hours
                    frac, whole = math.modf(track_ln.diff_end_time)
                    early_by_time = track_ln.diff_end_time
                    actual_unit = 'hours'
                    if round(frac, 2) > 0:
                        actual_unit = 'minutes'
                        early_by_time = round(track_ln.diff_end_time * 60)

                    # Find Penalties Entry as per the Early By Time
                    entries_values_early = self.env['hr.penalty.entries'].search([
                        ('actual_time', '=', early_by_time),
                        ('penalty_type_id', '=', early_pn.id),
                        ('actual_time_unit', '=', actual_unit)
                    ], limit=1)

                    # Calculate Penalties as per the time matched in Penalty Entry
                    if entries_values_early:
                        value_type = False
                        value = entries_values_early.calculated_time
                        amount = 0.0
                        if entries_values_early.calculated_time_unit == 'days':
                            amount = track_ln.employee_id.penalty_rate * early_pn.rate * entries_values_early.calculated_time * worked_hours * track_ln.employee_id.hourly_rate
                            value_type = 'days'
                        elif entries_values_early.calculated_time_unit == 'hours':
                            amount = track_ln.employee_id.penalty_rate * early_pn.rate * entries_values_early.calculated_time * track_ln.employee_id.hourly_rate
                            value_type = 'hours'
                        else:
                            amount = track_ln.employee_id.penalty_rate * early_pn.rate * (entries_values_early.calculated_time / 60) * track_ln.employee_id.hourly_rate
                            value_type = 'minutes'
                        penalty_vals.update({
                            'amount': amount,
                            'value_type': value_type,
                            'value': value,
                        })
                        penalty_obj.create(penalty_vals)
