from odoo import models,fields


class ChangeJobPosition(models.Model):
    _name = 'change.job.position.wiz'
    _description = 'This wizard is used for change the job position of employee.'

    new_job_position = fields.Many2one('hr.job', string="New Job Position")
    changing_date = fields.Date(string='Changing Date', default=fields.date.today())
    status = fields.Selection([('promotion', 'Promotion'), ('demotion', 'Demotion')], 'Status')

    def update_job_position(self):
        admission_id = self.env.context.get('active_id')
        rec = self.env['hr.employee'].browse(admission_id)
        self.env['job.history.line'].create({
                    'new_job_position': self.new_job_position.id,
                    'changing_date': self.changing_date,
                    'history_id': admission_id,
                    'status': self.status})
        rec.job_id = self.new_job_position.id
