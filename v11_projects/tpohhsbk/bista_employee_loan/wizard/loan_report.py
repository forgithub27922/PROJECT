from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PayslipDetailsReport(models.AbstractModel):
    _name = 'report.bista_employee_loan.report_loan'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'bista_employee_loan.report_loan')
        loan_ids = self.get_data(data)
        return {
            'doc_ids': self.env["loan.report.print"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': loan_ids,
            'data': data,

        }

    def get_data(self, data):
        loan_ids = []
        from_date = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
        to_date = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
        domain = [('company_id', '=', self.env.user.company_id.id), ('loan_issuing_date', '>=', from_date),
                  ('loan_issuing_date', '<=', to_date), ('state', '=', 'approved')]
        employee_loan_obj = self.env['hr.employee.loan']
        if data.get('employee_ids'):
            domain.append(('employee_id', 'in', data.get('employee_ids')))
        if data.get('department_ids'):
            domain.append(('department_id', 'in', data.get('department_ids')))
        for loan_rec in self.env['hr.employee.loan'].search(domain):
            employee_loan_obj += loan_rec

        if not employee_loan_obj:
            raise ValidationError(_("No Loan record found!"))
        return employee_loan_obj


class LoanSummaryReport(models.AbstractModel):
    _name = 'report.bista_employee_loan.report_loan_summary'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'bista_employee_loan.report_loan_summary')
        loan_ids = []
        from_date = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
        to_date = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
        employee_loan_obj = self.env['hr.employee.loan']
        group_by_department = {}
        for employee in data.get('employee_ids'):
            employee_loan_obj += self.env['hr.employee.loan'].search([('employee_id', '=', employee),
                                                                      ('state', '=', 'approved'),
                                                                      ('loan_issuing_date', '>=', from_date),
                                                                      ('loan_issuing_date', '<=', to_date),
                                                                      ])

        new_dept = list(set([x.department_id.id for x in employee_loan_obj]))
        if not employee_loan_obj:
            raise ValidationError(_("No Loan record found!"))

        for loan in employee_loan_obj.filtered(lambda l:l.department_id):
            group_by_department.setdefault(loan.department_id,[])
            if loan not in group_by_department[loan.department_id]:
                group_by_department[loan.department_id] += loan

        return {
            'doc_ids': self.env["loan.report.print"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': employee_loan_obj,
            'data': self.env['hr.department'].browse(new_dept),
            'group_by_department':group_by_department,

        }


class LoanReportPrint(models.Model):
    _name = 'loan.report.print'
    _description = 'Loan Report'

    company_id = fields.Many2one('res.company', string='Company')
    department_ids = fields.Many2many('hr.department', 'loan_department_rel',
                                      string="Department's")
    employee_ids = fields.Many2many('hr.employee', 'loan_employee_rel',
                                    string="Employee's")
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    report_type = fields.Selection([('detail', 'Detailed'),
                                    ('summary', 'Summary')],
                                   copy=False,
                                   required=1,
                                   default='detail',
                                   string='Report Type')

    @api.multi
    def check_loan_report(self):
        """
        get loan report line
        :return:
        """
        if self.date_to < self.date_from:
            raise ValidationError(_("Please Enter Proper Date Range."))
        datas = {
            'ids': self.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_ids':self.employee_ids and self.employee_ids.ids or False,
            'department_ids':self.department_ids and self.department_ids.ids or False
        }
        return self.env.ref('bista_employee_loan.action_loan_report'). \
            report_action(self, data=datas)

    @api.multi
    def check_loan_report_summary(self):
        if self.date_to < self.date_from:
            raise ValidationError(_("Please Enter Proper Date Range."))

        """
        get loan summary report
        :return:
        """
        all_dept = False
        if self.department_ids:
            all_dept = self.department_ids.ids
        else:
            all_dept = self.env['hr.department'].search([('company_id', '=', self.env.user.company_id.id)]).ids
        all_emp = self.env['hr.employee'].search([('department_id', 'in', all_dept)]).ids
        datas = {
            'ids': self.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_ids':all_emp,
            'department_ids':all_dept,
        }
        return self.env.ref('bista_employee_loan.'
                            'action_loan_summmary_report'). \
            report_action(self, data=datas)


class loan_installment_report(models.TransientModel):
    _name = 'loan.installment.report'
    _description = 'Loan Installment Report'

    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id.id)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    @api.multi
    def print_loan_installment_report(self):
        if self.date_to < self.date_from:
            raise ValidationError (_('Please enter proper date range.'))
        loan_installment_ids = self.env['loan.installments'].search_count([('due_date','>=',self.date_from),
        ('due_date','<=',self.date_to),('state','=','done')])

        if loan_installment_ids == 0:
            raise ValidationError(_("No Loan Installlment record found!"))

        datas = {'loan_installment_ids':loan_installment_ids,'doc_ids':self._ids}
        return self.env.ref('bista_employee_loan.''action_loan_installment_report').report_action(self,data=datas)


class loan_installment_report_template(models.AbstractModel):
    _name = 'report.bista_employee_loan.report_loan_installment_template'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env.ref('bista_employee_loan.report_loan_installment_template')
        record_id = self.env["loan.installment.report"].browse(data['doc_ids'])
        loan_installment_ids = self.env['loan.installments'].search([('due_date','>=',record_id.date_from),
        ('due_date','<=',record_id.date_to),('state','=','done')],order='loan_id')

        department_wise_installment = {}

        for loan_installment in loan_installment_ids.sorted(lambda x: x.loan_id.department_id,reverse=False):
            department_wise_installment.setdefault(loan_installment.loan_id.department_id,[])

            department_wise_installment[loan_installment.loan_id.department_id].append(loan_installment)

        return {
            'doc_ids': record_id,
            'doc_model': report.model,
            'docs': record_id,
            'data': data,
            'loan_installment_ids':loan_installment_ids,
            'department_wise_installment':sorted(department_wise_installment.items(),key=lambda key: key[0].id),
        }
