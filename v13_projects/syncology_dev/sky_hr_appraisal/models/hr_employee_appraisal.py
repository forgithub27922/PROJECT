#########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api


class EmployeeKRA(models.Model):
    _name = 'hr.employee.kra'
    _description = 'Employee Key Result Area'

    kra_id = fields.Many2one('hr.kra', 'KRA')
    kra_option_id = fields.Many2one('hr.kra.options', 'Result')
    employee_appraisal_id = fields.Many2one('hr.employee.appraisal', 'Employee Appraisal')


class EmployeeAppraisal(models.Model):
    _name = 'hr.employee.appraisal'
    _description = 'Employee Appraisal'
    _rec_name = 'employee_id'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_reviewee_name_arabic(self):
        for appraisal in self:
            appraisal.reviewee_arabic_name = str(appraisal.employee_id.first_name_arabic) + " " + str(appraisal.employee_id.middle_name_arabic) + " " + str(appraisal.employee_id.last_name_arabic) + " " + str(appraisal.employee_id.fourth_name_arabic)

    @api.depends('reviewer_id.first_name_arabic', 'reviewer_id.middle_name_arabic', 'reviewer_id.last_name_arabic', 'reviewer_id.fourth_name_arabic')
    def _compute_reviewer_name_arabic(self):
        for appraisal in self:
            appraisal.reviewer_arabic_name = str(appraisal.reviewer_id.first_name_arabic) + " " + str(appraisal.reviewer_id.middle_name_arabic) + " " + str(appraisal.reviewer_id.last_name_arabic) + " " + str(appraisal.reviewer_id.fourth_name_arabic)

    employee_id = fields.Many2one('hr.employee', 'Reviewee')
    reviewee_arabic_name = fields.Char('Reviewee (Arabic)', compute="_compute_reviewee_name_arabic", tracking=True, store=True)
    reviewer_id = fields.Many2one('hr.employee', 'Reviewer')
    reviewer_arabic_name = fields.Char('Reviewer (Arabic)', compute="_compute_reviewer_name_arabic", tracking=True, store=True)
    date = fields.Date('Date', default=fields.Date.today())
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', 'Job Position', related='employee_id.job_id')
    hike_percentage = fields.Float('Hike Percentage', compute='_calc_hike_percentage_new_salary')
    current_salary = fields.Float('Current Salary')
    scored_bonus = fields.Float('Scored Bonus', compute='_calc_scored_bonus')
    current_annual_bonus = fields.Float('Current Annual Bonus')
    new_salary = fields.Float('New Salary', compute='_calc_hike_percentage_new_salary')
    kra_ids = fields.One2many('hr.employee.kra', 'employee_appraisal_id', 'KRAs')
    state = fields.Selection([('pending', 'Pending'),
                              ('approve', 'Approve'),
                              ('reject', 'Reject')], 'Status', default='pending')

    @api.onchange('employee_id', 'hike_percentage')
    def onchange_emp(self):
        """
        This method will set the reviewer, current salary and annual bonus for employee
        -------------------------------------------------------------------------------
        @param self: object pointer
        :return:
        """
        self.reviewer_id = self.employee_id.parent_id.id
        self.current_salary = self.employee_id.salary
        self.current_annual_bonus = self.employee_id.annual_bonus

    def action_approve(self):
        """
        This method will set the state of the appraisal to approve
        ----------------------------------------------------------
        @param self: object pointer
        """
        for appraisal in self:
            appraisal.employee_id.sudo().write({'salary': appraisal.new_salary})
            appraisal.sudo().write({'state': 'approve'})

    def action_reject(self):
        """
        This method will set the state of the appraisal to reject
        ----------------------------------------------------------
        @param self: object pointer
        """
        self.sudo().write({'state': 'reject'})

    @api.depends('hike_percentage', 'current_annual_bonus')
    def _calc_scored_bonus(self):
        """
       This method will calculate the Scored Bonus
       -------------------------------------------------------------
       @param self: object pointer
       """
        for appraisal in self:
            appraisal.scored_bonus = appraisal.hike_percentage * appraisal.current_annual_bonus

    @api.depends('kra_ids', 'employee_id')
    def _calc_hike_percentage_new_salary(self):
        """
        This method will calculate the Hike Percentage and New Salary
        -------------------------------------------------------------
        @param self: object pointer
        """
        obt_result = sum([appraisal.kra_option_id.value for appraisal in self.kra_ids])
        total_res = 0
        for appraisal in self:
            if len(appraisal.kra_ids) > 0:
                for kra in appraisal.kra_ids:
                    total_res += kra.kra_id.option_ids and max(kra.kra_id.option_ids.mapped('value')) or 0

                if total_res != 0.0:
                    appraisal.hike_percentage = obt_result / total_res
                    appraisal.new_salary = appraisal.current_salary + appraisal.hike_percentage * appraisal.current_annual_bonus
                else:
                    appraisal.hike_percentage = 0.0
                    appraisal.new_salary = 0.0

            else:

                appraisal.hike_percentage = 0.0
                appraisal.new_salary = 0.0
