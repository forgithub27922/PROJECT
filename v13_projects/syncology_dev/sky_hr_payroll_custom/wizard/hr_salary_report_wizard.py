# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
import xlsxwriter
import base64


class HrSalaryReportWizard(models.TransientModel):
    _name = 'hr.salary.report.wizard'
    _description = 'Hr Salary Report Wizard'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    salary_fields = fields.Boolean('Penalties and Additions')
    employee_ids = fields.Many2many('hr.employee', string='employees')

    def print_salary_report(self):
        """
        This method will print the XLS report for employees
        -------------------------------------------------------------------
        @param self: object pointer
         """

        attach_obj = self.env['ir.attachment']
        wb = xlsxwriter.Workbook('/tmp/hr_salary_report.xlsx')
        ws = wb.add_worksheet('employee salaries')
        header_format = wb.add_format({'bold': True})

        ws.write(0, 0, 'Name', header_format)
        ws.write(0, 1, 'salary', header_format)
        ws.write(0, 2, 'Additions Amount', header_format)
        ws.write(0, 3, 'Gross Salary', header_format)
        ws.write(0, 4, 'Paycuts Amount', header_format)
        ws.write(0, 5, 'Net Salary', header_format)
        ws.write(0, 6, 'Start Date', header_format)
        ws.write(0, 7, 'End Date', header_format)

        dom = ['&', ('start_date', '>=', self.start_date), ('end_date', '<=', self.end_date)]

        employees = self.employee_ids

        if not employees.ids:
            employees = self.env['hr.employee'].sudo().search([])

        if not self.user_has_groups('sky_hr_payroll_custom.group_payroll_manager'):
            employees = employees.filtered(lambda r: r.is_confidential == False)
        dom += [('employee_id', 'in', employees.ids)]

        salaries = self.env['hr.employee.salary'].sudo().search(dom)

        row = 1
        for sal in salaries:
            row += 1
            ws.set_column(0, 9, 15)
            ws.write(row, 0, sal.employee_id.display_name, header_format)
            ws.write(row, 1, sal.basic)
            ws.write(row, 2, sal.additions)
            ws.write(row, 3, sal.gross)
            ws.write(row, 4, sal.paycuts)
            ws.write(row, 5, sal.net)
            ws.write(row, 6, str(sal.start_date))
            ws.write(row, 7, str(sal.end_date))

            if self.salary_fields:
                data_format = wb.add_format({'size': 10, 'bold': True})
                if sal.addition_ids:
                    row += 1
                    ws.write(row, 0, 'Additions', data_format)
                    ws.write(row, 1, 'Date', data_format)
                    ws.write(row, 2, 'Addition type', data_format)
                    ws.write(row, 3, 'Type of Value', data_format)
                    ws.write(row, 4, 'Value', data_format)
                    ws.write(row, 5, 'amount', data_format)
                    ws.write(row, 6, 'Issued By', data_format)
                    ws.write(row, 7, 'Reason', data_format)
                    for addition in sal.addition_ids:
                        row += 1
                        ws.write(row, 1, str(addition.date))
                        ws.write(row, 2, addition.addition_type_id.name)
                        ws.write(row, 3, addition.type_of_value)
                        ws.write(row, 4, addition.value)
                        ws.write(row, 5, addition.amount)
                        ws.write(row, 6, addition.issued_by.name)
                        ws.write(row, 7, addition.reason)

                if sal.penalty_ids:
                    row += 1
                    ws.write(row, 0, 'Penalties', data_format)
                    ws.write(row, 1, 'Date', data_format)
                    ws.write(row, 2, 'Penalty Type', data_format)
                    ws.write(row, 3, 'Value Type', data_format)
                    ws.write(row, 4, 'Value', data_format)
                    ws.write(row, 5, 'amount', data_format)
                    ws.write(row, 6, 'Issued By', data_format)
                    ws.write(row, 7, 'Reason', data_format)
                    for penalty in sal.penalty_ids:
                        row += 1
                        ws.write(row, 1, str(penalty.date))
                        ws.write(row, 2, penalty.penalty_type_id.name)
                        ws.write(row, 3, penalty.value_type)
                        ws.write(row, 4, penalty.value)
                        ws.write(row, 5, penalty.amount)
                        ws.write(row, 6, penalty.issued_by.name)
                        ws.write(row, 7, penalty.reason)
                row += 1

        wb.close()
        f1 = open('/tmp/hr_salary_report.xlsx', 'rb')
        xls_data = f1.read()
        buf = base64.b64encode(xls_data)
        doc = attach_obj.create({'name': '%s.xlsx' % ('Salary Report'),
                                 'datas': buf,
                                 'res_model': 'hr.salary.report.wizard',
                                 'store_fname': '%s.xlsx' % ('Salary Report'),
                                 })

        return {'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true' % (doc.id),
                'target': 'current',
                'close_on_report_download': True,
                }
