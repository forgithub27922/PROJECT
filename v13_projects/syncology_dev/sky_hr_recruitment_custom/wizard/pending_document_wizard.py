# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _


class PendingDocument(models.TransientModel):
    _name = 'pending.document'
    _description = 'Pending Document'

    job_id = fields.Many2one('hr.job', 'Job Title')
    manager_id = fields.Many2one('hr.employee', 'Direct Manager')
    department_id = fields.Many2one('hr.department', 'Department')
    child_ids = fields.Many2many('hr.employee', string='Subordinates')
    working_schedule_id = fields.Many2one('resource.calendar', 'Working Schedule')
    starting_date = fields.Date('Starting Date')
    salary = fields.Float('Salary')
    annual_bonus = fields.Float('Annual Bonus')
    next_salary_date = fields.Date('Next Salary Date')
    addition_rate = fields.Float('Addition Rate', default=1)
    penalty_rate = fields.Float('Penalty Rate', default=1)

    @api.onchange('department_id')
    def onchange_dept(self):
        """
        This will set the working schedule as per the department.
        ---------------------------------------------------------
        @param self: object pointer
        :return:
        """
        for wiz in self:
            wiz.working_schedule_id = wiz.department_id.working_schedule_id.id

    @api.model
    def default_get(self, fields):
        """
        Overridden default_get method to fetch job position from applicant.
        -------------------------------------------------------------------
        @param self: object pointer
        @pram fields: list of fields which has default values
        :return : a dictionary containing fields and default values
        """
        res = super(PendingDocument, self).default_get(fields)
        current_id = self.env.context.get('active_id')
        applicant = self.env['hr.applicant'].browse(current_id)
        res['job_id'] = applicant.job_id.id
        return res

    def action_confirm(self):
        current_id = self.env.context.get('active_id')
        applicant = self.env['hr.applicant'].browse(current_id)
        vals = {
            'job_id': self.job_id.id,
            'manager_id': self.manager_id.id,
            'department_id': self.department_id.id,
            'working_schedule_id': self.working_schedule_id.id,
            'starting_date': self.starting_date,
            'salary': self.salary,
            'annual_bonus': self.annual_bonus,
            'child_ids': [(6, 0, self.child_ids.ids)],
            'next_salary_date': self.next_salary_date,
            'addition_rate': self.addition_rate,
            'penalty_rate': self.penalty_rate,
            'state': 'accepted'

        }
        applicant.write(vals)
        template = self.env.ref('sky_hr_recruitment_custom.accept_applicant_email_template')
        email_value = {'email_to': applicant.email_from, 'email_from': self.env.user.email or ''}
        template.send_mail(self.id, email_values=email_value, force_send=True,
                           notif_layout='sky_hr_recruitment_custom.sky_mail_template')
