

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    company_id = fields.Many2one('res.company', string='Company')
    department_ids = fields.Many2many('hr.department', 'hr_department_group_rel', 'payslip_id', 'department_id', 'Department')
    job_ids = fields.Many2many('hr.job', 'hr_job_group_rel', 'payslip_id', 'job_id', 'Designation')

    @api.multi
    def compute_sheet(self):
        employee_recs = False
        emp_obj = self.env['hr.employee']
        department_ids = self.department_ids.ids
        job_ids = self.job_ids.ids
        if self.employee_ids.ids:
            employee_recs = self.employee_ids
        elif not self.employee_ids and job_ids:
            employee_recs = emp_obj.search([('job_id', 'in', job_ids), ('company_id', '=', self.company_id.id)])
        elif not self.employee_ids and not job_ids and department_ids:
            employee_recs = emp_obj.search([('department_id', 'in', department_ids), ('company_id', '=', self.company_id.id)])
        elif not self.employee_ids and not job_ids and not department_ids:
            employee_recs = emp_obj.search(
                [('company_id', '=', self.company_id.id)])
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note','name','journal_id'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        journal_id = run_data.get('journal_id')
        data['employee_ids'] = employee_recs.ids
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            if not employee.contract_id:
                raise UserError(
                    _("Contract is missing for :%s") % (
                    employee.name,))
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            existing_payslip = self.env['hr.payslip'].search_count([('employee_id', '=', employee.id), ('payslip_run_id', '=', active_id)])
            if existing_payslip >= 1:
                raise UserError(_('Payslip of %s already existing in %s Batch.') % (employee.name,run_data['name']))

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': employee.contract_id.struct_id.id or False,
                'contract_id':employee.contract_id.id or False,
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
                'journal_id':journal_id[0] ,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}


class HrJob(models.Model):
    _inherit = 'hr.job'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if self._context.get('department_ids'):
            department_ids = self._context.get('department_ids')[0][2]
            if department_ids:
                job_ids = self.env['hr.job'].search([('department_id', 'in', department_ids)]).ids

                domain = [('id', 'in', job_ids)]
        else:
            if self._context.get('company_id'):
                company_id = self._context.get('company_id')
                if company_id:
                    job_ids = self.env['hr.job'].search(
                        [('company_id', '=', company_id)]).ids
                domain = [('id', '=', job_ids)]
        return super(HrJob, self).name_search(name, args + domain,
                                              operator=operator,
                                              limit=limit)


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if self._context.get('designation_ids'):
            designation_ids = self._context.get('designation_ids')[0][2]
            if designation_ids:
                emp_ids = self.env['hr.employee'].search([('job_id', 'in', designation_ids)]).ids
                domain = [('id', 'in', emp_ids)]
        elif self._context.get('department_ids'):
            department_ids = self._context.get('department_ids')[0][2]
            if department_ids:
                dept_emp_ids = self.env['hr.employee'].search([('department_id', 'in', department_ids)]).ids
                domain = [('job_id', 'in', dept_emp_ids)]
        else:
            if self._context.get('company_id'):
                company_id = self._context.get('company_id')
                if company_id:
                    emp_ids = self.env['hr.employee'].search(
                        [('company_id', '=', company_id)]).ids
                domain = [('id', '=', emp_ids)]
        return super(Employee, self).name_search(name, args + domain,
                                                 operator=operator,
                                                 limit=limit)

