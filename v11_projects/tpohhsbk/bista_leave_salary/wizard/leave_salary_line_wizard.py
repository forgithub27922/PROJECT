# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import datetime


class LeaveSalaryLineWizard(models.TransientModel):
    _name = 'leave.salary.line.wizard'

    leave_request_ids = fields.Many2many("hr.holidays",string="Leave Request")

    @api.onchange('leave_request_ids')
    def onchange_leave_request_ids(self):
        if self._context.get('active_id'):
            leave_salary = self.env['leave.salary'].browse(self._context.get('active_id'))
            requests = leave_salary.leave_salary_line_ids.mapped('leave_request_id').ids
            domain = [
                ('type','=','remove'), ('lapse_leave','=',False),
                ('is_leave_adjustment','=',False),
                ('employee_id','=',leave_salary.employee_id.id),
                ('id','not in',requests),('state','=','validate'),
                ('leave_salary_paid','=',False)]
            if leave_salary.is_accrued:
                domain.append(('holiday_status_id.accruals','=',True))
            else:
                domain.append(('holiday_status_id.accruals','=',False))

            request_ids = self.env['hr.holidays'].search(domain).ids
            result = {'domain':{'leave_request_ids':[('id','in',request_ids)]}}
            return result

    @api.multi
    def add_lines(self):
        salary_lines_obj = self.env['leave.salary.line']
        extra_lines = salary_lines_obj.search([('leave_salary_id','=',False)])
        if extra_lines:
            extra_lines.unlink()
            
        for req in self.leave_request_ids:
            req_start_date = req.date_from and datetime.datetime.strptime(req.date_from, '%Y-%m-%d').date()
            req_end_date = req.date_to and datetime.datetime.strptime(req.date_to, '%Y-%m-%d').date()
            
            if not req_start_date.month == req_end_date.month:
                start_date = datetime.datetime.strptime(req_end_date.strftime('%Y-%m-01'), '%Y-%m-%d')
                end_date = (start_date - datetime.timedelta(seconds=1)).date()
                vals1 = {
                        'leave_salary_id' : self._context.get('active_id'),
                        'leave_request_id' : req.id,
                        'start_date' : req_start_date,
                        'end_date'  : end_date,
                        'no_of_days' : (end_date - req_start_date).days + 1,
                        'employee_id' : req.employee_id.id
                        }
                
                vals2 = {
                        'leave_salary_id' : self._context.get('active_id'),
                        'leave_request_id' : req.id,
                        'start_date' : start_date,
                        'end_date' : req_end_date,
                        'no_of_days': (req_end_date - start_date.date()).days + 1,
                        'employee_id' : req.employee_id.id
                        }
                salary_lines_obj.create(vals1)
                salary_lines_obj.create(vals2)
                                
            else:
                salary_lines_vals = {
                                'leave_salary_id' : self._context.get('active_id'),
                                'leave_request_id' : req.id,
                                'start_date' : req.date_from,
                                'end_date' : req.date_to,
                                'employee_id' : req.employee_id.id
                                }
                salary_lines_obj.create(salary_lines_vals)
            
