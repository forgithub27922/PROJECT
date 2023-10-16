from odoo import models, fields, api


class CancelApplicantWizard(models.TransientModel):
    _name = 'cancel.applicant.wizard'
    _description = 'Cancel Applicant Wizard'

    reason = fields.Text('Reason')
    job_id = fields.Many2one('hr.job', 'Job Title')

    @api.model
    def default_get(self, fields):
        """
        Overridden default_get method to fetch job position from applicant.
        -------------------------------------------------------------------
        @param self: object pointer
        @pram fields: list of fields which has default values
        :return : a dictionary containing fields and default values
        """
        res = super(CancelApplicantWizard, self).default_get(fields)
        current_id = self.env.context.get('active_id')
        applicant = self.env['hr.applicant'].browse(current_id)
        res['job_id'] = applicant.job_id.id
        return res

    def cancel_applicant_interview(self):
        """
        This method will send an email to the applicant regarding cancellation
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        active_id = self.env.context.get('active_id')
        applicant = self.env['hr.applicant'].browse(active_id)
        template = self.env.ref('sky_hr_recruitment_custom.cancel_applicant_email_template')
        email_value = {'email_to': applicant.email_from, 'email_from': self.env.user.email or ''}
        template.send_mail(self.id, email_values=email_value, force_send=True,
                           notif_layout='sky_hr_recruitment_custom.sky_mail_template')
        applicant.state = 'canceled'
