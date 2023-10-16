from odoo import models, fields, api, _
from datetime import datetime,date
import calendar
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_path
import base64
import xlsxwriter
import tempfile
import os


class EmployeeWorkingDaysReportWizard(models.TransientModel):
    _name = 'emp.working.days.report.wiz'
    _description = 'Emloyee Working Days Of Year Wizard'

    report_by = fields.Selection([('by_year', 'By Year'),
                                  ('by_month', 'By Month'),
                                  ('by_date', 'By Date')],
                                  'Report By', default='by_year')
    year = fields.Integer('Year', default=datetime.now().year)
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], 'Month')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    name = fields.Char('File Name')
    file_download = fields.Binary('File to Download')
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='Status', readonly=True, default='init')

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        """
        This method is used to check the dates
        --------------------------------------
        @param self: object pointer
        """
        for rep in self:
            if (rep.start_date and rep.end_date) and rep.start_date > rep.end_date:
                raise ValidationError(_('The start date must be prior to the end date!'))

    def print_report(self):
        """
        This method is used to calculate the total worked days of an employee
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        attch_obj = self.env['ir.attachment']
        file_path = tempfile.NamedTemporaryFile().name
        workbook = xlsxwriter.Workbook(file_path + '.xlsx')
#         workbook = xlsxwriter.Workbook('employee_working_days_report.xls')
        worksheet = workbook.add_worksheet('Working Days')
        title_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'font_size': 18, 'bold': True})
        header_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'font_size': 12, 'bold': True,
             'bg_color': '#808080', 'border': True})
        data_format = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'font_size': 10, 'border': True})
        module_path = get_module_path('hr_time_tracking')
        module_path += '/static/image/company_logo.png'
        worksheet.merge_range(0, 0, 2, 1, "")
        worksheet.insert_image(0, 0, module_path, {'x_scale': 0.5, 'y_scale': 0.5})
        worksheet.merge_range(0, 2, 2, 7, "Employee Working Days Report", title_format)
        for wiz in self:
            # Get the start date and end date to be used in report
            if wiz.report_by == 'by_year':
                # Get the first date and last date of the year
                st_dt = date(wiz.year, 1, 1)
                en_dt = date(wiz.year, 12, 31)
            elif wiz.report_by == 'by_month':
                # Get the first date and last date of the month
                month = int(wiz.month)
                wd_md = calendar.monthrange(wiz.year, month)
                st_dt = date(wiz.year, month, 1)
                en_dt = date(wiz.year, month, wd_md[1])
            elif wiz.report_by == 'by_date':
                # Get the start date and end date from wizard
                st_dt = wiz.start_date
                en_dt = wiz.end_date
            str_dt = st_dt.strftime('%Y-%m-%d')
            end_dt = en_dt.strftime('%Y-%m-%d')
            worksheet.write(4, 0, 'Start Date', header_format)
            worksheet.write(4, 1, str_dt, data_format)
            worksheet.write(5, 0, 'End Date', header_format)
            worksheet.write(5, 1, end_dt, data_format)
            worksheet.set_column(0, 0, 60)
            worksheet.set_column(0, 1, 20)
            # Get Employees
            employee_ids = wiz.employee_ids.ids
            # Fetch worked days in specific period
            query = '''select count(t.id),t.employee_id, e.name 
            from time_tracking_line t, hr_employee e 
            where t.employee_id = e.id
            and t.present=True
            and t.date between %s and %s'''
            params = (str_dt, end_dt)
            if employee_ids:
                query += ''' and t.employee_id in %s'''
                params = (str_dt, end_dt, tuple(employee_ids))
            query += '''group by t.employee_id,e.name'''
            self._cr.execute(query, params)
            res = self._cr.fetchall()
            # Print it in the Excel report
            row = 7
            worksheet.write(row, 0, 'Employee', header_format)
            worksheet.write(row, 1, 'Working Days', header_format)
            row += 1
            for rec in res:
                worksheet.write(row, 0, rec[2], data_format)
                worksheet.write(row, 1, rec[0], data_format)
                row += 1
            workbook.close()
            
            buf = base64.encodestring(open(file_path + '.xlsx', 'rb').read())
            try:
                if buf:
                    os.remove(file_path + '.xlsx')
            except OSError:
                pass
    
            attach_ids = attch_obj.search([('res_model', '=',
                                            'emp.working.days.report.wiz')])
            if attach_ids:
                try:
                    attach_ids.unlink()
                except:
                    pass
            doc_id = attch_obj.create({'name': '%s.xlsx' % ('Employee Working Days Report'),
                                       'datas': buf,
                                       'res_model': 'emp.working.days.report.wiz'
                                                    'wizard',
                                       'store_fname': '%s.xlsx' % (
                                       'Employee Working Days Report'),
                                       })
            return {'type': 'ir.actions.act_url',
                    'url': 'web/content/%s?download=true' % (doc_id.id),
                    'target': 'current',
                    }
#             self.write({
#                 'state': 'done',
#                 'file_download': base64.b64encode(open('employee_working_days_report.xls', 'rb').read()),
#                 'name': 'employee_working_days_report.xls'
#             })
# 
#             return {
#                 'name': 'Employee Working Days Report',
#                 'type': 'ir.actions.act_window',
#                 'res_model': self._name,
#                 'view_mode': 'form',
#                 'view_type': 'form',
#                 'res_id': self.id,
#                 'target': 'new'
#             }