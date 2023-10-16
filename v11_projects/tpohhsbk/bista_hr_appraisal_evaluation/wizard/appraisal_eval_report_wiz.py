from odoo import models, fields, api


class AppraisalParse(models.AbstractModel):
    _name = 'report.bista_hr_appraisal_evaluation.app_eval_report'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'bista_hr_appraisal_evaluation.app_eval_report')
        # loan_ids = self.get_data(data)
        return {
            # 'doc_ids': self.env["appraisal.evaluation.report.wizard"].
            # browse(data["ids"]),
            'doc_model': report.model,
            'docs': self.env['hr.appraisal.configuration'].browse(1),
            'data': data,

        }


class AppraisalEvalRepor(models.TransientModel):
    _name = "appraisal.evaluation.report.wizard"

    appraisal_template_id = fields.Many2one(
        'hr.appraisal.configuration',
        string='Appraisal Template')

    appraisal_period_id = fields.Many2one(
        'hr.appraisal.configuration.period', string='Appraisal Period')

    employee_ids = fields.Many2many('hr.employee', string='Employees')

    @api.multi
    def print_pdf(self):
        datas = {'ids': self.id,
                 'employee_ids': self.employee_ids.ids,
                 'appraisal_template_id': self.appraisal_template_id or False,
                 'appraisal_period_id': self.appraisal_period_id or False,
                 }
        return self.env.ref(
            'bista_hr_appraisal_evaluation.action_appraisal_eval_report').\
            report_action(self, data=datas)
