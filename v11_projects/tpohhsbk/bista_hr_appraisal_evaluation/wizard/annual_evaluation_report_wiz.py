from odoo import fields, models, api


class AnnualEvaluationWiz(models.TransientModel):
    _name = "annual.evaluation.report.wizard"

    appraisal_template_id = fields.Many2one(
        'hr.appraisal.configuration',
        string='Appraisal Template')
    appraisal_period_ids = fields.Many2many(
        'hr.appraisal.configuration.period',
        'annual_eval_report_hr_appr_config_period_rel',
        string='Appraisal Period')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    order_by = fields.Selection([
        ('employee', 'Employee'), ('appraisal_period', 'Appraisal Period')],
        'Order By', default='employee')

    @api.onchange('appraisal_template_id')
    def onchange_appraisal_template_id(self):
        if self.appraisal_template_id:
            self.appraisal_period_ids = \
                self.appraisal_template_id.app_eval_ids.ids

    def generate_annual_evaluation_report(self):
        """
        generate annual evaluation report
        :return:
        """
        if self.appraisal_template_id:
            appraisal_period_ids = self.appraisal_period_ids.ids
            employee_ids = self.employee_ids.ids
            if not appraisal_period_ids:
                appraisal_period_ids = \
                    self.appraisal_template_id.app_eval_ids.ids
            if not employee_ids:
                employee_ids = self.env['hr.employee'].search([]).ids
            query = """SELECT id FROM hr_employee_kra WHERE 
            appraisal_template_id=%s AND appraisal_period_id in (%s) AND 
            employee_id in (%s)""" % (
                self.appraisal_template_id.id, ','.join(
                    map(str, appraisal_period_ids)), ','.join(
                    map(str, employee_ids)))
            if self.order_by == 'appraisal_period':
                query += ' ORDER BY appraisal_period_id'
            else:
                query += ' ORDER BY employee_id'
            self.env.cr.execute(query)
            x = self.env.cr.fetchall()
            appraisal_evaluation_ids = []
            if x:
                [appraisal_evaluation_ids.append(a[0]) for a in x]
                return self.env.ref(
                    'bista_hr_appraisal_evaluation.'
                    'action_annual_appraisal_report').report_action(
                    appraisal_evaluation_ids, data={})
