from odoo import models, fields, api


class UpdateScheduleInterviewWizard(models.TransientModel):
    _name = 'update.schedule.interview.wizard'
    _description = 'Update Schedule Interview Wizard'

    interview_date = fields.Date('Interview Date')
    interview_time = fields.Float('Interview Time')
    interview_location = fields.Char('Interview Location')

    def update_schedule_interview(self):
        """
        This method is used to schedule an interview for applicant
        ----------------------------------------------------------
        @param self: object pointer
        """
        active_id = self.env.context.get('active_id')
        applicant = self.env['hr.applicant'].browse(active_id)
        interview_obj = self.env["hr.interview"]
        # Schedule Interview
        interview_vals = {
            'interview_date': self.interview_date,
            'interview_time': self.interview_time,
            'interview_location': self.interview_location,
            'applicant_id': applicant.id
        }
        interview = interview_obj.create([interview_vals])
        # Send email for interview
        template = self.env.ref('sky_hr_recruitment_custom.schedule_interview_email_template')
        email_value = {'email_to': applicant.email_from, 'email_from': self.env.user.email or ''}
        template.send_mail(interview.id, email_values=email_value, force_send=True,
                           notif_layout='sky_hr_recruitment_custom.sky_mail_template')
        applicant.state = 'pending_for_interview'
