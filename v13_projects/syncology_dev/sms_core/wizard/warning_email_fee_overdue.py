# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from datetime import date
from odoo.tools.mail import append_content_to_html


class SendWarningEmail(models.TransientModel):
 
    _name = 'fee.overdue.warning.email.wizard'
    _description = 'fee.overdue.warning.email.wizard'
    
    @api.onchange('installment_id')
    def call_warning_email_wizard(self):
        self.student_ids = None
        listt =[]
        fee_ids = self.env['student.fee'].search([('fee_policy_line_id', '=', self.installment_id.id),('status', '=','unpaid')])
        for fee in fee_ids:
#             print("is over ue",fee.is_overdue)
#             if fee.is_overdue:
            fee_dictt = (0, 0, {'student_id':fee.student_id.id,  'status':'unpaid','applied_fee':fee.applied_fee, 'due_date': fee.due_date,'is_overdue':fee.is_overdue})
            listt.append(fee_dictt)
        if len(listt)>0:
            self.student_ids = listt
        return
    
    @api.onchange('warning_date')
    def check_email_status_onchange(self):
        if self.warning_date:
            if self.warning_date <= date.today():
                self.email_status = 'ok'
            else:
                self.email_status = 'cant_send'
        else:
            raise UserError(_('Warning date not set on installment.'))
        return

    installment_id = fields.Many2one('fee.policy.line')
    intallment_name = fields.Char('Installment Name')
    student_ids = fields.Many2many('student.fee', string='Fee Records')
    warning_date = fields.Integer(string='Warning Date', related='installment_id.warning_email_date')
    due_date = fields.Date('Due Date', related='installment_id.due_date')
    email_status = fields.Selection([('ok', 'Ok'), ('cant_send', 'Can\'t send before warning date')], string='Email Status')

    def send_fee_overdue_warning_email(self):
        print("method called........")
        if len(self.student_ids)<1:
            raise UserError(_('No Overdue records found'))
        
        inst_id = self.env.context.get('installment_id', False)
        rec = self.env['fee.policy.line'].browse(inst_id)
        print("this is rec ========= ",rec)
        fee_ids = self.env['student.fee'].search([('fee_policy_line_id', '=', inst_id),('status','=','unpaid')])
        if self.email_status == 'ok':
            res = self.env['student.fee'].overdue_warning_email(fee_ids)
        else:
            raise UserError(_('Can\'t send email before warning date.'))
        return
