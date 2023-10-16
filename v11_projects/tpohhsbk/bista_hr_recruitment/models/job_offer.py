# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class JobOffer(models.Model):
    _name = "hr.job.offer"
    _description = "Job Offer"
    _rec_name = "applicant_name"

    state = fields.Selection(
        selection=[('draft', 'Draft'), ('hr_manager', 'HR Manager'),
                   ('approved', 'Approved'), ('cancel','Cancelled')],
        default='draft')
    applicant_id = fields.Many2one(comodel_name="hr.applicant",
                                   string="Application For", required=True)
    applicant_name = fields.Char(related="applicant_id.partner_name",
                                 store=True, string="Applicant")
    description = fields.Char(string="Description")
    date_validity = fields.Date(string="Date Validity")
    proposed_by_id = fields.Many2one('res.users', string="Proposed By",
                                     default=lambda self: self.env.user)
    amount = fields.Float(string="Basic (Per Month)")
    ctc_amount = fields.Float(string="Gross Salary")
    struct_id = fields.Many2one('hr.payroll.structure',
                                string='Salary Structure')
    job_revision_ids = fields.One2many('hr.job.revision',
                                       inverse_name="offer_id",
                                       string="Revision")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    reason = fields.Char(string='Reason')
    salary_detail_id = fields.Many2one('hr.salary.offer.details', string="Salary Detail ID")


    def approve_by_hr(self):
        '''
        To set state hr_manager
        :return:
        '''
        self.approve_job()
        self.write({'state': 'hr_manager'})


    def approve_by_mngr(self):
        '''
        To set state approved
        :return:
        '''
        self.approve_job()
        self.write({'state': 'approved'})


    def compute_salary(self):
        self.ensure_one()
        if not self.amount:
            raise ValidationError(_('Basic amount must be greater than zero.'))
        if not self.struct_id:
            raise ValidationError(_('Please select Salary Structure.'))
        ### Create offer salary details.
        employee_record = contract_record = payslip_record = False
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        payslip_obj = self.env['hr.payslip']
        sal_offer_detail_obj = self.env['hr.salary.offer.details']
        date_result = self.date_validity or fields.date.today()

        employee_record = employee_obj.create({
            'name': 'Dummy - Job Offer Employee',
            'job_id': self.applicant_id and self.applicant_id.job_id
                      and self.applicant_id.job_id.id or False
        })
        if employee_record:
            contract_record = contract_obj.create({
                'name': 'Dummy - Job Offer Contract',
                'employee_id': employee_record.id or False,
                'struct_id': self.struct_id and self.struct_id.id or False,
                'wage': self.amount,
            })
        if employee_record and contract_record and self.struct_id:
            payslip_record = payslip_obj.create({
                'employee_id': employee_record.id or False,
                'date_from': date_result,
                'date_to': date_result,
                'contract_id': contract_record.id or False,
                'struct_id': self.struct_id and self.struct_id.id or False,
            })
            payslip_record.compute_sheet()

            line_data = []
            for line in payslip_record.line_ids:
                line_data.append(
                    (0, 0, {'name': line.name,
                            'code': line.code,
                            'sequence': line.sequence,
                            'category_id': line.category_id.id or False,
                            'salary_rule_id': line.salary_rule_id and
                                              line.salary_rule_id.id or False,
                            'company_id': self.company_id
                                          and self.company_id.id or False,
                            'total': line.total
                            }))
                if line.code == 'NET':
                    self.write({'ctc_amount': line.total})
            if line_data:
                salary_detail_rec = sal_offer_detail_obj.create({
                    'name': self.applicant_name,
                    'date': date_result,
                    'struct_id': self.struct_id and self.struct_id.id or False,
                    'company_id': self.company_id
                                  and self.company_id.id or False,
                    'salary_detail_lines': line_data
                })
                self.write({'salary_detail_id': salary_detail_rec.id or False})
        if payslip_record:
            payslip_record.unlink()
        if contract_record:
            contract_record.unlink()
        if employee_record:
            employee_record.unlink()




    def reset_to_draft(self):
        '''
        To reset to draft
        :return:
        '''
        self.approve_job()
        self.write({'state': 'draft'})
    

    def cancel(self):
        '''
        To reset to draft
        :return:
        '''
        # self.approve_job()
        for rec in self:
            view_id = self.env.ref('bista_hr_recruitment.wiz_view_reject_job_form')
            return {
                'name': 'Cancel Offer',
                'type': 'ir.actions.act_window',
                'view_id': view_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wiz.reject.job.offer',
                'target': 'new',
            }

    def approve_job(self):
        '''
        To create revision history
        :return:
        '''
        vals = {'approved_by_id': self.env.user.id,
                'approved_date': fields.date.today(),
                'offer_id': self.id}
        self.env['hr.job.revision'].create(vals)


class JobRevision(models.Model):
    _name = "hr.job.revision"
    _description = "Job Revision"

    approved_by_id = fields.Many2one('res.users', string="Approved By")
    approved_date = fields.Date(string="Date")
    offer_id = fields.Many2one('hr.job.offer', string="Job Offer")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
