from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class KraGenerateWiz(models.TransientModel):
    _name = 'hr.kra.generate.wiz'

    appraisal_template_id = fields.Many2one(
        'hr.appraisal.configuration',
        related='appraisal_period_id.appraisal_template_id',
        string='Appraisal Template')
    appraisal_period_id = fields.Many2one(
        'hr.appraisal.configuration.period', string='Appraisal Period')
    review_start_date = fields.Date(string='Start Date')
    review_end_date = fields.Date(string='End Date')
    self_review_date = fields.Date("Self Review End Date")
    mngr_pr_review_date = fields.Date("Manager/Peers Review End Date")
    employee_ids = fields.Many2many('hr.employee', string='Employees')

    @api.onchange('appraisal_period_id')
    def onchange_appraisal_period(self):
        """
        set default value based on onchange of period
        :return:
        """
        if self.appraisal_period_id:
            self.review_start_date = self.appraisal_period_id.date_start
            self.review_end_date = self.appraisal_period_id.date_end

    @api.onchange('review_end_date')
    def onchange_review_end_date(self):
        """
        set default value based on onchange of end date
        :return:
        """
        self.self_review_date = self.review_end_date
        self.mngr_pr_review_date = self.review_end_date

    @api.constrains('self_review_date', 'mngr_pr_review_date')
    def date_validations(self):
        """
        Date Validations
        :return:
        """
        start_date = self.appraisal_period_id.date_start
        end_date = self.appraisal_period_id.date_end
        if self.self_review_date < start_date or self.self_review_date > \
                end_date:
            raise ValidationError(
                'The self evaluation date must be within start date and end '
                'date')
        elif self.mngr_pr_review_date < start_date or \
                self.mngr_pr_review_date > end_date:
            raise ValidationError(
                'The manager/peers evaluation date must be within start date '
                'and end date')
        elif self.mngr_pr_review_date < self.self_review_date:
            raise ValidationError(
                'The manager/peers evaluation date must be greater than or '
                'equal to self evaluation date')

    @api.model
    def _get_related_window_action_id(self, data_obj):
        """
        get window action for email link
        :param data_pool:
        :return:
        """
        window_action_id = \
            data_obj.get_object_reference(
                'bista_hr_appraisal_evaluation', 'hr_employee_kra_action')[
                1] or False
        return window_action_id

    @api.multi
    def generate_appraisal_records(self):
        """
        generate employee appraisal records.
        :return:
        """
        employee_recs = self.employee_ids
        if not employee_recs:
            employee_recs = self.env['hr.employee'].search([])
        for emp_rec in employee_recs:
            if not emp_rec.job_id:
                raise ValidationError(_(
                    'Employee "%s" has no position kindly, contact to hr '
                    'team.') % (emp_rec.name))
            if not emp_rec.job_id.hr_kra_id:
                raise ValidationError(_(
                    'KRA not set on position "%s" Kindly, Contact to HR '
                    'team.') % (emp_rec.job_id.name))
            kra_line_lst = []
            for kra_line_rec in emp_rec.job_id.hr_kra_id.line_ids:
                kra_line_vals = {
                    'question': kra_line_rec.question,
                    'description': kra_line_rec.description,
                    'weightage': kra_line_rec.weightage,
                    'measurement_ids': [
                        (6, 0, kra_line_rec.measurement_ids.ids)]}
                kra_line_lst.append((0, 0, kra_line_vals))
            # name = self.env['ir.sequence'].next_by_code('hr.employee.kra')
            code = self.env['ir.sequence'].next_by_code('hr.employee.kra')
            current_year = datetime.now().date().year
            curr_id = self.appraisal_period_id.name.split(' ')
            name = 'KRA/' + str(current_year) + "/" + str(
                curr_id[2]) + "/" + code
            kra_vals = {
                'name': name,
                'employee_id': emp_rec.id,
                'job_id': emp_rec.job_id.id,
                'appraisal_template_id': self.appraisal_template_id.id,
                'appraisal_period_id': self.appraisal_period_id.id,
                'review_start_date': self.appraisal_period_id.date_start,
                'review_end_date': self.appraisal_period_id.date_end,
                'self_review_date': self.self_review_date,
                'mngr_pr_review_date': self.mngr_pr_review_date,
                'kra_line_ids': kra_line_lst,
                'assessment_type': 'self_assessment',
            }
            employee_kra_rec = self.env['hr.employee.kra'].create(kra_vals)
            # set manager and peers
            if emp_rec.parent_id:
                employee_kra_rec.reviewer_ids = [
                    (6, 0, [emp_rec.parent_id.id])]
            peers_ids = self.env['hr.employee'].search([
                ('parent_id', '=', emp_rec.id)]).ids
            employee_kra_rec.peers_ids = [(6, 0, peers_ids)]
            # send email notification
            display_link = False
            data_obj = self.env['ir.model.data']
            action_id = self._get_related_window_action_id(data_obj)
            if action_id:
                display_link = True
            template_obj = self.env['mail.template']
            template_id = data_obj.get_object_reference(
                'bista_hr_appraisal_evaluation',
                'hr_generate_appraisal_email_temp')[1]
            template_rec = template_obj.browse(template_id)
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url.static')
            if template_rec:
                ctx = {
                    'email_to': '',
                    'base_url': base_url,
                    'display_link': display_link,
                    'action_id': action_id,
                    'model': 'hr.employee.kra'
                }
                template_rec.with_context(ctx).send_mail(
                    employee_kra_rec.id, force_send=False)
