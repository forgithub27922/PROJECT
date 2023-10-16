# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class Interviewer(models.Model):
    _name = 'hr.interview'
    _description = "Interview"
    _rec_name = 'interviewer_id'

    interviewer_id = fields.Many2one('res.users', string="Interviewer")
    applicant_id = fields.Many2one('hr.applicant', "Applicant")
    overall_score_ids = fields.One2many(
        'total.overall.score', 'interviewer_id', string="Score Details")
    stage_id = fields.Many2one('hr.recruitment.stage', string="Stage")
    moi_id = fields.Many2one('mode.of.interview', string="Mode Of Interview")
    date_of_interview = fields.Datetime(string="Date Of Interview")
    overall_comment = fields.Text(string="Overall Comment")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.depends('overall_score_ids.achieved_score')
    def count_score(self):
        """Count the total score and achieved score and result from overall
        score line."""
        
        for each_data in self:
            avg_score = 0.0
            scored_points = 0.0
            scored_points = sum([int(each_one.achieved_score) for each_one
                                 in each_data.overall_score_ids])
            if scored_points:
                avg_score = scored_points / len(each_data.overall_score_ids)
                avg_score = round(avg_score)
            if avg_score:
                each_data.scored_points = avg_score
                each_data.result = str(avg_score)

    scored_points = fields.Float(compute='count_score', string="Scored Points")
    result = fields.Selection([('0', '0'), ('1', 'Poor'),
                               ('2', 'Satisfactory'),
                               ('3', 'Average'),
                               ('4', 'Good'),
                               ('5', 'Excellent')], string="Result",
                              compute='count_score')


class Applicant(models.Model):
    _inherit = "hr.applicant"

    interviewer_ids = fields.One2many('hr.interview', 'applicant_id',
                                      string="Interviewer")
    interviewer_user_ids = fields.Many2many(
        'res.users', 'interviewer_user_ids', string="Interviewers")
    hr_document_ids = fields.One2many('applicant.hr.document', 'applicant_id',
                                      string="HR Documents")
    overall_avg_score = fields.Float(string='Overall Average',
                                     compute="compute_avg_score", store=True)

    @api.onchange('interviewer_user_ids')
    def onchange_interviewers(self):
        """Onchange of Interviewer M2m field it will add or remove line
        in Interviewer O2m field."""
        list_iv = []
        exist_rec_ids = self.interviewer_ids.ids
        exist_interviewer_ids = self.interviewer_ids.mapped(
            'interviewer_id').ids

        # To add line in hr.interviewer
        for each_data in self.interviewer_user_ids.filtered(
                lambda data: data.id not in exist_interviewer_ids):
            if each_data.id not in exist_interviewer_ids:
                interview_rec = self.env['hr.interview'].create({
                    'applicant_id': self.id,
                         'interviewer_id': each_data.id,
                         'stage_id': self.stage_id.id,
                })
                list_iv.append(interview_rec.id)
        list_iv.extend(exist_rec_ids)
        # to remove lines from hr.interviewer
        for rec_unlink in self.interviewer_ids:
            if rec_unlink.interviewer_id.id not in \
                    self.interviewer_user_ids.ids:
                list_iv.remove(rec_unlink.id)
        # To replace all new records
        self.interviewer_ids = [(6, 0, list_iv)]
        
    @api.constrains('interviewer_user_ids')
    def remove_interview_lines(self):
        self.env['hr.interview'].search([('applicant_id', '=', False)]).unlink()
        

    def get_filtered_job_offer(self):
        """
        To return job offer for applicant
        :return: Action with filter domain
        """
        self.ensure_one()
        action = self.env.ref('bista_hr_recruitment.hr_job_offer_action')
        return {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': self._context,
            'domain': [('applicant_id', '=', self.id)],
            'res_model': action.res_model,
        }

    @api.depends('stage_id')
    def compute_stage_id(self):
        """From the stage, change Tab Interview and field document made
        visible/invisble."""
        
        for each_data in self:
            if each_data.stage_id and each_data.stage_id.is_interview:
                each_data.is_interviewer = True
#                 for iv_line in each_data.interviewer_ids:
#                     iv_line.write({'stage_id': self.stage_id.id})
            else:
                each_data.is_interviewer = False
            if each_data.stage_id and each_data.stage_id.is_document:
                each_data.is_document = True
            else:
                each_data.is_document = False
            if each_data.stage_id and each_data.stage_id.is_job_offer:
                each_data.is_job_offer = True
            else:
                each_data.is_job_offer = False

    is_document = fields.Boolean(compute="compute_stage_id", stting="Document")
    is_interviewer = fields.Boolean(compute="compute_stage_id",
                                    string="Is Interviewer")
    is_job_offer = fields.Boolean(compute="compute_stage_id",
                                  string="Job Offer")

    @api.depends('interviewer_ids.scored_points',
                 'interviewer_ids.overall_score_ids')
    def compute_avg_score(self):
        """
        To calculate final average score for applicant
        :return:
        """
        for candidate in self:
            avg_score = 0
            if len(candidate.interviewer_ids) > 0:
                avg_score += sum(candidate.sudo().interviewer_ids.mapped(
                    'scored_points'))
            try:
                avg_score = avg_score / len(candidate.sudo().interviewer_ids)
            except ZeroDivisionError:
                pass
            candidate.overall_avg_score = avg_score


    def send_mail(self):
        '''
        :return: Send mail to Interviewers.
        '''
        self.ensure_one()
        template_id = self.env.ref(
            'bista_hr_recruitment.interviewer_notification_template')
        if template_id:
            for interviewer_rec in self.interviewer_ids:
                interviewer = interviewer_rec.interviewer_id
                if interviewer and interviewer.partner_id and \
                    interviewer.partner_id.email:
                    email_to = interviewer.partner_id.email
                    if email_to:
                        job = self.job_id and self.job_id.name or ''
                        department = self.department_id and \
                                     self.department_id.name or ''

                        body = '''<![CDATA[
<div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
    <p>Dear ''' + str(interviewer.name) + ''',</p>
    <p>This mail is to inform you for conduct interview.</p><br/>

    <p>Applicant' details as given below:</p>
    <p><b>Applicant's Name: </b>''' + str(self.partner_name or '') + '''</p>
    <p><b>Email: </b>''' + str(self.email_from or '') + '''</p>
    <p><b>Phone: </b>''' + str(self.partner_phone or '') + '''</p>
    <p><b>Mobile: </b>''' + str(self.partner_mobile or '') + '''</p><br/>

    <p><b>Job Profile:</b></p>
    <p><b>Applied For: </b>''' + str(job) + '''</p>
    <p><b>Department: </b>''' + str(department) + '''</p><br/>

    <p>Have a nice day.</p>
    <p>Warm regards.</p>
</div>
'''

                        template_id.write({'email_to': email_to,
                                           'body_html': body})
                        template_id.send_mail(self.id, force_send=True)
        return True

    @api.model
    def create(self, vals):
        result = super(Applicant, self).create(vals)
        if not vals.get('activity_date_deadline'):
            result.write({'activity_date_deadline': fields.Date.today()})
        return result


    def write(self, vals):
        if not vals.get('activity_date_deadline'):
            vals.update({'activity_date_deadline': fields.Date.today()})
        return super(Applicant, self).write(vals)


class Recruitment(models.Model):
    _inherit = 'hr.recruitment.stage'

    is_interview = fields.Boolean(string="Interview")
    is_document = fields.Boolean(string="Document")
    is_job_offer = fields.Boolean(string="Job Offer")


class ModeOfInterview(models.Model):
    _name = 'mode.of.interview'

    name = fields.Char("Name")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class TotalOverallScore(models.Model):
    _name = 'total.overall.score'

    name = fields.Char("Name")
    interviewer_id = fields.Many2one('hr.interview', "Interviewer")
    description = fields.Char("Description")
    comment = fields.Char("Comment")
    achieved_score = fields.Selection([('0', '0'), ('1', 'Poor'),
                                       ('2', 'Satisfactory'),
                                       ('3', 'Average'), ('4', 'Good'),
                                       ('5', 'Excellent')],
                                      string="Achieved Score", default='1')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class ApplicantHRDocument(models.Model):
    _inherit = 'applicant.hr.document'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant")


    def get_report(self):
        """
        Print hr documents like appointment letter, offer letter etc.
        :return: report action
        """
        hr_doc = self.env['hr.job.document'].browse(self.document_id.id)
        if self.document_id and self.applicant_id and self.applicant_id.id:
            hr_doc.applicant_id = self.applicant_id.id
        return self.env.ref(
            'hr_document.report_offer_letter').report_action(hr_doc)
