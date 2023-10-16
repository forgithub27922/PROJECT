from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Leave(models.Model):
    _inherit = 'hr.leave'

    penalty_id = fields.Many2one('hr.penalty.type', 'Penalty')
    penalty_value = fields.Integer('Value')
    penalty_unit = fields.Selection([('days', 'Days'), ('hours', 'Hours'), ('minutes', 'Minutes')], 'Unit')

    @api.constrains('date_from', 'date_to', 'state', 'employee_id', 'start_time', 'end_time')
    def _check_date(self):
        for holiday in self:
            exists_leave = self.sudo().search([
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('end_time', '>', holiday.start_time),
                ('start_time', '<', holiday.end_time),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse'])
            ])
            if exists_leave:
                start_time = "{:.2f}".format(exists_leave.start_time)
                end_time = "{:.2f}".format(exists_leave.end_time)
                raise ValidationError(_(
                    """You are not allowed to add Leave Request because you have another %s leave"""
                    """ with overlapping time %s to %s on the same day."""
                ) % (exists_leave.holiday_status_id.name, start_time , end_time))

    def calc_penalty_amount(self, penalty_type, penalty_value, penalty_unit):
        """
        This method will calculate the penalty amount for the penalty.
        --------------------------------------------------------------
        :param penalty_type: Type of Penalty
        :param penalty_value: Type of penalty value (hours,minutes,days)
        :param penalty_unit: The value of penalty in integer
        :return: Amount of the Penalty
        """
        calc_unit = penalty_unit
        calc_value = penalty_value
        amount = 0.0
        # If the Penalty has the Penalty Configuration
        if penalty_type.penalty_entries.ids:
            # Get working hours
            worked_hours = self.employee_id.count_working_hours(
                employee_id=self.employee_id,
                date=self.date_from
            )

            # Find Penalties Entry as per the Late By Time
            penalty_entry = penalty_type.penalty_entries.filtered(
                lambda rec: rec.actual_time == penalty_value and rec.actual_time_unit == penalty_unit
            )
            # Calculate Penalties as per the time matched in Penalty Entry
            if penalty_entry.ids:
                calc_value = penalty_entry.calculated_time
                calc_unit = penalty_entry.calculated_time_unit
        # Calculate Penalty Rate
        pen_rate = self.employee_id.penalty_rate * penalty_type.rate * self.employee_id.hourly_rate
        # Calculate Amount
        if calc_unit == 'hours':
            amount = pen_rate * calc_value
        if calc_unit == 'days':
            amount = pen_rate * calc_value * worked_hours
        elif calc_unit == 'minutes':
            amount = pen_rate * calc_value / 60
        # Return amount, value and unit to create the penalty
        return amount, calc_value, calc_unit

    def create_penalty(self, penalty_type, penalty_value, penalty_unit, tracking_line=False):
        """
        This method will create a penalty with attached leave type
        ----------------------------------------------------------
        @param self: object pointer
        @param penalty_type: Type of Penalty
        @param penalty_value: The value of penalty
        @param penalty_unit: The unit of Penalty
        @param tracking_line: Tracking line where this penalty should be added
        """
        penalty_obj = self.env['hr.penalty']
        for rec in self:
            penalty_vals = {
                'employee_id': rec.employee_id.id,
                'date': rec.request_date_from,
                'penalty_type_id': penalty_type.id,
                'reason': rec.name,
                'tracking_line_id': tracking_line and tracking_line.id,
            }
            # Calculate Amount of Penalty
            amount, calc_value, calc_unit = rec.calc_penalty_amount(penalty_type, penalty_value, penalty_unit)
            # Update the penalty vals with the penalty calculated values
            penalty_vals.update({
                'amount': amount,
                'value_type': calc_unit,
                'value': calc_value,
            })
            # Create a penalty
            penalty_obj.create(penalty_vals)

    def action_approve(self):
        """
        Overridden method of leave and vacation approval to create a penalty for paycut
        ----------------------------------------------------------------------------------------
        @param self : object pointer
        """
        res = super(Leave, self).action_approve()
        tracking_line_obj = self.env['time.tracking.line']
        for rec in self:
            if rec.state == 'validate':
                tracking_line = tracking_line_obj.search([('employee_id', '=', rec.employee_id.id),
                                                          ('date', '=', rec.request_date_from)], limit=1)
                leave_type = rec.leave_type
                penalty_type = rec.penalty_id
                if tracking_line and tracking_line.penalty_ids.ids:
                    if leave_type == 'leave':
                        penalty = tracking_line.penalty_ids.filtered(
                            lambda rec: rec.penalty_type_id == penalty_type)
                        if penalty.ids:
                            if penalty.state == 'approved':
                                raise UserError(_('You have a penalty approved, you need to cancel this penalty'))
                            elif penalty.state == 'rejected':
                                rec.create_penalty(rec.penalty_id, rec.penalty_value, rec.penalty_unit, tracking_line)
                            # Calculate Amount of Penalty
                            amount, calc_value, calc_unit = rec.calc_penalty_amount(rec.penalty_id, rec.penalty_value,
                                                                                    rec.penalty_unit)
                            # Update the penalty with the penalty calculated values
                            penalty.write({
                                'value_type': calc_unit,
                                'value': calc_value,
                                'amount': amount
                            })
                        else:
                            rec.create_penalty(penalty_type, rec.penalty_value, rec.penalty_unit, tracking_line)
                    else:
                        penalty = tracking_line.penalty_ids.filtered(
                            lambda rec: rec.penalty_type_id == penalty_type)
                        if penalty.ids:
                            if penalty.state == 'approved':
                                raise UserError(_('You have a penalty approved, you need to cancel this penalty'))
                            elif penalty.state == 'rejected':
                                rec.create_penalty(penalty_type, rec.penalty_value, rec.penalty_unit, tracking_line)
                            # Calculate Amount of Penalty
                            amount, calc_value, calc_unit = rec.calc_penalty_amount(rec.penalty_id,
                                                                                    rec.penalty_value,
                                                                                    rec.penalty_unit)
                            # Update the penalty with the penalty calculated values
                            penalty.write({
                                'value_type': calc_unit,
                                'value': calc_value,
                                'amount': amount
                            })
                        else:
                            rec.create_penalty(penalty_type, rec.penalty_value, rec.penalty_unit, tracking_line)
                else:
                    if rec.leave_type == 'leave':
                        rec.create_penalty(penalty_type, rec.penalty_value, rec.penalty_unit, tracking_line)
                    else:
                        rec.create_penalty(penalty_type, rec.penalty_value, rec.penalty_unit, tracking_line)
        return res
