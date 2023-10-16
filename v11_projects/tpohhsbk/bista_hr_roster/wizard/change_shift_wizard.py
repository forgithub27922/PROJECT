# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime


class ChangeShiftWizard(models.TransientModel):

    _name = 'change.shift.wizard'

    shift_id = fields.Many2one('hr.shift.code', string="Shift Code")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.multi
    def action_change_shift(self):
        """change roster shift code from start date to end date"""
        for data in self:
            start_date = data.start_date
            end_date = data.end_date
            if start_date > end_date:
                raise UserError("End date should be greater then start date.")
            today = datetime.strftime(datetime.now().date(), DF)
            if today > start_date:
                raise UserError("Back dated shift change not allowed.")
            attendance_count = self.env['hr.attendance'].search([
                ('check_in', '>=', start_date), ('check_out', '<=', end_date)], limit=1)
            if attendance_count:
                raise UserError("Attendance found for date %s. \n\
                Can not change shift" % (attendance_count.check_in))
            hr_roster_obj = self.env['hr.roster']
            # This part is calling from two object one s for single employee
            #  and other oone for bulk employee so we need to distinguished
            # using context
            domain = False
            if self._context.get('bulk_roster_id'):
                hr_roster_id = hr_roster_obj.search(
                    [('bulk_roster_id', '=' , self._context.get('bulk_roster_id'))])
                domain = [('shift_code_id', '!=', False),
                     ('schedule_date', '>=', start_date),
                     ('schedule_date', '<=', end_date),
                     ('roster_id', 'in', hr_roster_id.ids)]
            if self._context.get('active_model') == 'hr.roster':
                hr_roster_id = hr_roster_obj.browse(self._context.get(
                    'active_id'))
                domain = [('shift_code_id', '!=', False),
                          ('schedule_date', '>=', start_date),
                          ('schedule_date', '<=', end_date),
                          ('roster_id', 'in', hr_roster_id.ids)]
            roster_line =\
                self.env['hr.roster.line'].search(domain)
            # get roster.vs.attendance.line when shift change based on duration
            roster_vs_att_lines = self.env['roster.vs.attendance.line'].search(
                [('roster_line_id', 'in', roster_line.ids),
                 ('att_date', '>=', start_date),
                 ('att_date', '<=', end_date)
                 ])
            # update roster.vs.attendance.line based on duration
            roster_vs_att_lines.write({
                'planned_sign_in': data.shift_id.time_in,
                'planned_sign_out': data.shift_id.time_out})
            roster_line.write({'shift_code_id': data.shift_id.id})
