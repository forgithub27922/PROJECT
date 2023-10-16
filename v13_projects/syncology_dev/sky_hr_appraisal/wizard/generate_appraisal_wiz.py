from odoo import models, fields, api


class GenerateAppraisalWizard(models.TransientModel):
    _name = 'gen.appr.wiz'
    _description = 'Generate Appraisal Wizard'

    date = fields.Date('Date', default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', 'Reviewee')
    manager_id = fields.Many2one('hr.employee', 'Reviewer')
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Job Position')
    kra_ids = fields.Many2many('hr.kra', string='KRAs')
    old_salary = fields.Float('Current Salary')
    old_annual_bonus = fields.Float('Current Annual Bonus')

    @api.model
    def default_get(self, fields):
        """
        Overridden default_get method to fetch default values for employee
        ------------------------------------------------------------------
        @param self: object pointer
        @param fields: list of fields with default value
        :return: A dictionary containing fields and default values
        """
        emp_obj = self.env['hr.employee']
        res = super(GenerateAppraisalWizard, self).default_get(fields)
        emp_id = self._context.get('active_id', False)
        emp = emp_obj.browse(emp_id)
        res.update({
            'employee_id': emp.id,
            'manager_id': emp.parent_id.id,
            'department_id': emp.department_id.id,
            'job_id': emp.job_id.id,
            'old_salary': emp.salary,
            'old_annual_bonus': emp.annual_bonus
        })
        return res

    def generate_appraisal(self):
        """
        This method will generate the appraisal form for employee
        ---------------------------------------------------------
        @param self: object pointer
        :return: Action of form of appraisal
        """
        appr_obj = self.env['hr.employee.appraisal']
        appr_vals = {
            'employee_id': self.employee_id.id,
            'reviewer_id': self.manager_id.id,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
            'date': self.date,
            'current_salary': self.old_salary,
            'current_annual_bonus': self.old_annual_bonus,
            'state': 'pending',
            'kra_ids': [(0, 0, {'kra_id': kra.id,}) for kra in self.kra_ids]
        }
        appr = appr_obj.sudo().create([appr_vals])
        appr_action = self.env.ref('sky_hr_appraisal.action_employee_appraisal').read()[0]
        form_view = self.env.ref('sky_hr_appraisal.view_hr_employee_appraisal_form')
        appr_action['views'] = [(form_view.id, 'form')]
        appr_action['res_id'] = appr.id
        return appr_action