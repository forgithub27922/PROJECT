# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class HrVisa(models.Model):
    _inherit = 'hr.visa'

    is_notification_sent = fields.Boolean(string='Is Notification Sent?')


class HrDocument(models.Model):
    _inherit = 'hr.document'

    is_notification_sent = fields.Boolean(string='Is Notification Sent?')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _visa_expiry_date_scheduler(self):
        for company in self.env.user.company_ids:
            today_date = datetime.now().date()
            expired_recs = self.env['hr.visa'].search([('date_end', '<=', today_date), ('company_id', '=', company.id),
                                                       ('status', '!=', 'expired')])
            for rec in expired_recs:
                rec.write({'status':'expired', 'active':False})

#             expiry_date = today_date + relativedelta(days=+15)
#             upcoming_expiry_recs = \
#                 self.env['hr.visa'].search([('date_end', '<=', expiry_date),
#                                             ('is_notification_sent', '=', False),
#                                             ('company_id', '=', company.id),
#                                             ('status', '!=', 'expired')])
#             template_id = self.env.ref(
#                 'hr_employee_notification.visa_expiry_date_template')
#             self.send_email(template_id, upcoming_expiry_recs, company)
        return True

    @api.model
    def _document_expiry_date_scheduler(self):
        for company in self.env['res.company'].search([]):
            today_date = datetime.now().date()
            expired_recs = self.env['hr.document'].search([('date_expiry', '<=', today_date), ('company_id', '=', company.id),
                                                           ('status', '!=', 'expired')])
            for rec in expired_recs:
                rec.write({'status': 'expired', 'active': False})

            expiry_date = today_date + relativedelta(months=+1)
            upcoming_expiry_recs = self.env['hr.document'].search([('date_expiry', '<=', expiry_date),
                                                                   ('is_notification_sent', '=', False),
                                                                   ('company_id', '=', company.id),
                                                                   ('status', '!=', 'expired')])
            template_id = self.env.ref('hr_employee_notification.document_expiry_date_template')
            self.send_email(template_id, upcoming_expiry_recs, company)
        return True

    def send_email(self, template_id, upcoming_expiry_recs, company_id):
        group_users = self.env.ref('bista_hr.group_pr_department').users
        users = group_users.filtered(lambda r: r.company_id.id == company_id.id)
        for user in users:
            email_lst = [user.email for user in filter(lambda x: x.email, user)]
            email_to = ','.join(map(str, email_lst))
            for rec in upcoming_expiry_recs:
                rec.is_notification_sent = True
                if template_id:
                    template_id.write({'email_to': email_to})
                    template_id.send_mail(rec.id, force_send=True)


class Holidays(models.Model):
    _inherit = "hr.holidays"

    is_notification_sent = fields.Boolean(string='Is Notification Sent?')

    def _leave_expiry_notify_scheduler(self):
        # Make Commented Code for Leave Expiry Email Notification.
#         ICPSudo = self.env['ir.config_parameter'].sudo()
#         if ICPSudo.get_param('allow_leave_expiry_notification'):
#             today_date = datetime.now().date()
#             expiry_date = today_date + relativedelta(months=+1)
#             expiry_recs = self.search([('date_to', '<=', expiry_date),
#                                        ('type', '=', 'add'),
#                                        ('is_notification_sent', '=', False),
#                                        ('state', '=', 'validate')])
#             template_id = self.env.ref(
#                 'hr_employee_notification.leave_expiry_notification_template')
#             for rec in expiry_recs:
#                 ctx = dict(rec._context)
#                 taken_leaves_recs = self.search(
#                     [('employee_id', '=', rec.employee_id.id),
#                      ('type', '=', 'remove'),
#                      ('date_from', '>=', rec.date_from),
#                      ('date_to', '<=', rec.date_to),
#                      ('state', '=', 'validate'),
#                      ('holiday_status_id', '=',
#                       rec.holiday_status_id.id)])
#                 taken_leave_no = 0
#                 for taken_leave in taken_leaves_recs:
#                     taken_leave_no += taken_leave.number_of_days_temp
#                 remaining_leaves = rec.number_of_days_temp - taken_leave_no
#                 # if rec.compoff_date_expired:
#                 #     rec.update({'date_to': rec.compoff_date_expired})
#                 ctx.update({
#                     'remaining_leaves': remaining_leaves,
#                 })
#                 if template_id and remaining_leaves > 0:
#                     if rec.employee_id.work_email:
#                         template_id.write(
#                             {'email_to': rec.employee_id.work_email})
#                         template_id.with_context(ctx).send_mail(
#                             rec.id, force_send=True)
#                         rec.is_notification_sent = True
            return True
