# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from io import BytesIO
import base64
from odoo.tools.misc import xlwt
from datetime import datetime
from odoo.tools.misc import formatLang
import babel



class BankSoftCopyXls(models.TransientModel):
    _name = 'bank.soft.copy.xls'

    payslip_ids = fields.Many2many(
        'hr.payslip', 'rel_bank_soft_copy_xls', 'payslip_id',
        'bank_copy_id', 'Employee Payslip')

    @api.model
    def default_get(self, fields_list):
        res = super(BankSoftCopyXls, self).default_get(fields_list)
        if self._context.get('active_ids'):
            payslip_ids = []
            if self._context.get('active_model') == 'hr.payslip.run':
                for run in self.env['hr.payslip.run'].browse(
                        self._context.get('active_ids')):
                    payslip_ids += run.slip_ids.ids
            else:
                payslip_ids = self._context.get('active_ids')
            res.update({
                'payslip_ids': [(6, 0, payslip_ids)]})
        return res

    @api.model
    def set_header(self, worksheet):
        """
        Bank Soft Copy Header
        :param worksheet:
        :return:
        """
        # New Bank Soft Copy Report Format
        for c in range(0, 14):
            if c in [0,2,6,8,10,13]:
                worksheet.col(c).width = 256 * 30
            else:
                worksheet.col(c).width = 256 * 23
        worksheet.row(0).height = 600

        s1 = xlwt.easyxf(
            'font: bold 1, height 230;'
            'pattern: pattern solid, fore-colour green;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: wrap 1;'
            )

        worksheet.write(0, 0, 'Corp Reference Number', s1)
        worksheet.write(0, 1, 'Payment Type', s1)
        worksheet.write(0, 2, 'Debit Account number/Iban', s1)
        worksheet.write(0, 3, 'Amount', s1)
        worksheet.write(0, 4, 'Payment Currency', s1)
        worksheet.write(0, 5, 'Payment Value date', s1)
        worksheet.write(0, 6, 'Beneficiary Name', s1)
        worksheet.write(0, 7, 'Bene Address 1', s1)
        worksheet.write(0, 8, 'Bene Account Number', s1)
        worksheet.write(0, 9, 'Bene Bank Name', s1)
        worksheet.write(0, 10, 'Payment Details 1', s1)
        worksheet.write(0, 11, 'Charge', s1)
        worksheet.write(0, 12, 'Remmitance Code', s1)
        worksheet.write(0, 13, 'Remmitance Detail', s1)

    @api.model
    def set_lines_data(self, worksheet):
        """
        Bank Soft Copy Lines
        :param worksheet:
        :return:
        """
        # New Bank Soft Copy Report Format
        locale = self.env.context.get('lang') or 'en_US'
        row = 1
        for slip in self.payslip_ids.filtered(lambda l:l.employee_payment_journal_id and l.employee_payment_journal_id.type == 'bank' and not l.employee_payment_journal_id.is_ratibi\
                                              if l.state == 'paid' else l.employee_id.journal_id.type == 'bank' and not l.employee_id.journal_id.is_ratibi):
            col = 0
            acc_number = ''
            bank_name = ''
            if slip.employee_id.bank_account_id:
                acc_number = slip.employee_id.bank_account_id.acc_number
                if slip.employee_id.bank_account_id.bank_id:
                    bank_name = slip.employee_id.bank_account_id.bank_id.name

            worksheet.write(row, col+1, 'CST')
            worksheet.write(row, col + 2, acc_number)
            worksheet.write(row, col + 3, slip.net_amount)
            worksheet.write(row, col + 4, slip.company_id.currency_id.name)
            worksheet.write(row, col + 5, slip.date_from)
            worksheet.write(row, col + 6, slip.employee_id.name)
            worksheet.write(row, col + 7, 'Dubai')
            worksheet.write(row, col + 8, acc_number)
            worksheet.write(row, col + 9, bank_name)
            ttyme = datetime.strptime(slip.date_from, '%Y-%m-%d').date()
            payment_details_desc = ('Salary for the month of %s' % (tools.ustr(babel.dates.format_date(date=ttyme, format='MMM-yy', locale=locale))))
            worksheet.write(row, col + 10, payment_details_desc)
            worksheet.write(row, col + 11, 'Our')
            worksheet.write(row, col + 12, 'SAL')
            worksheet.write(row, col + 13, 'REF')
            row += 1

    @api.model
    def set_ratibi_header(self, worksheet):
        """
        set's header on RATIBI report.
        :param worksheet:
        :return:
        """
        # New RATIBI Format
        worksheet.row(0).height = 500
        s1 = xlwt.easyxf(
            'font: bold 1, height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: wrap 1;')
        worksheet.write(0, 0, 'Transaction Currency', s1)
        worksheet.write(0, 1, 'Beneficiary Account No.', s1)
        worksheet.write(0, 2, 'Payment Amount', s1)
        worksheet.write(0, 3, 'Employee ID', s1)
        worksheet.write(0, 4, 'Extra Info 1', s1)
        worksheet.write(0, 5, 'Extra Info 2', s1)
        worksheet.write(0, 6, 'Beneficiary Name', s1)

        worksheet.col(0).width = 256 * 14
        worksheet.col(1).width = 256 * 25
        worksheet.col(2).width = 256 * 14
        worksheet.col(2).width = 256 * 12
        worksheet.col(4).width = 256 * 29
        worksheet.col(5).width = 256 * 12
        worksheet.col(6).width = 256 * 26

    @api.model
    def set_ratibi_lines_data(self, worksheet):
        """
        set's lines on RATIBI report.
        :return:
        """
        row = 1
        s1 = xlwt.easyxf(
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: wrap 1;')

        # New RATIBI Format
        for slip in self.payslip_ids.filtered(lambda l:l.employee_payment_journal_id and l.employee_payment_journal_id.is_ratibi if l.state == 'paid' else l.employee_id.journal_id.is_ratibi):
            col = 0
            worksheet.write(row, col, slip.company_id.currency_id.name, s1)
            worksheet.write(row, col + 1, slip.employee_id.bank_account_id.acc_number, s1)
            worksheet.write(row, col + 2, slip.net_amount, s1)
            worksheet.write(row, col + 3, slip.employee_id.employee_code, s1)
            worksheet.write(row, col + 4, slip.payslip_run_id.name, s1)
            worksheet.write(row, col + 5, '', s1)
            worksheet.write(row, col + 6, slip.employee_id.name, s1)
            row += 1

    @api.model
    def set_procash_header(self, worksheet):
        """
        set's header on ProCash report.
        :param worksheet:
        :return:
        """
        # New Cash Salaries(Pro-cash) Report Format
        for c in range(0, 5):
            if c in [1,3]:
                worksheet.col(c).width = 256 * 30
            else:
                worksheet.col(c).width = 256 * 13

        worksheet.row(0).height = 500
        worksheet.row(1).height = 400
        worksheet.row(2).height = 400
        worksheet.row(3).height = 400

        header_merge_format = xlwt.easyxf(
            'font: bold 1, height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert centre, horiz center')

        normal_header_format = xlwt.easyxf(
            'font: height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert centre, horiz center')
        
        main_header_format = xlwt.easyxf(
            'font: bold 1, height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore_colour light_green;'
            'align: wrap on,vert centre, horiz center')

        worksheet.write_merge(0, 0, 0, 4, 'Office Of  H.H. Dr Sheikh Sultan Bin Khalifa Bin Zayed AL-Nahyan',header_merge_format)
        worksheet.write_merge(1, 1, 0, 4, 'Dubai',normal_header_format)

        record_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        locale = self.env.context.get('lang') or 'en_US'
        ttyme = datetime.strptime(record_id.date_start, '%Y-%m-%d').date()
        name = ('SALARY STATEMENT FOR %s' % (tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-Y', locale=locale))))
        worksheet.write_merge(2, 2, 0, 4, name,normal_header_format)
        worksheet.write_merge(3, 3, 0, 4, 'CASH SALARY',normal_header_format)

        worksheet.write(4, 0, 'S.NO', main_header_format)
        worksheet.write(4, 1, 'Salary Batch',main_header_format)
        worksheet.write(4, 2, 'ID', main_header_format)
        worksheet.write(4, 3, 'NAMES', main_header_format)
        worksheet.write(4, 4, 'SALARY', main_header_format)

    @api.model
    def set_procash_lines_data(self, worksheet):
        """
        set's lines on ProCash report.
        :param worksheet:
        :return:
        """
        # New Cash Salaries(Pro-cash) Report Format
        center_format = xlwt.easyxf(
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert centre, horiz center')
        left_format = xlwt.easyxf(
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: , horiz left')
        normal_format = xlwt.easyxf(
            'font:height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert center, horiz right')
        
        total_format = xlwt.easyxf(
            'font: bold 1, height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert centre, horiz left')

        total_amount_format = xlwt.easyxf(
            'font: bold 1, height 230;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'align: wrap on,vert centre, horiz right')

        record_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        row = 5
        total_amount = 0.00
        count= 1
        for slip in self.payslip_ids.filtered(lambda l:l.employee_payment_journal_id and l.employee_payment_journal_id.type == 'cash' \
                                              if l.state == 'paid' else l.employee_id.journal_id.type == 'cash'):
            worksheet.row(row).height = 300
            col = 0
            worksheet.write(row, col, count,center_format)
            worksheet.write(row, col + 1,record_id.name,left_format)
            worksheet.write(row, col + 2, slip.employee_id.employee_code,center_format)
            worksheet.write(row, col + 3, slip.employee_id.name,left_format)
            worksheet.write(row, col + 4, formatLang(self.env, slip.net_amount),normal_format)
            total_amount += slip.net_amount
            row += 1
            count +=1

        worksheet.row(row).height = 300
        worksheet.write(row, 0,'',total_format)
        worksheet.write(row, 1,'',total_format)
        worksheet.write(row, 2,'',total_format)
        worksheet.write(row, 3, "Total",total_format)
        worksheet.write(row, 4, formatLang(self.env, total_amount),total_amount_format)

    @api.multi
    def print_report(self):
        """
        Project Hours
        :return: {}
        """
        ctx = dict(self._context)
        workbook = xlwt.Workbook()
        xls_file_name = ''
        if ctx.get('report') == 'bnk_soft':
            worksheet = workbook.add_sheet('Bank Soft Copy')
            self.set_header(worksheet)
            self.set_lines_data(worksheet)
            xls_file_name = 'Bank Specific Report.xls'
        elif ctx.get('report') == 'ratibi':
            worksheet = workbook.add_sheet('RATIBI Card Transfer')
            self.set_ratibi_header(worksheet)
            self.set_ratibi_lines_data(worksheet)
            xls_file_name = 'RATIBI Card Transfer.xls'
        elif ctx.get('report') == 'procash':
            worksheet = workbook.add_sheet('ProCash')
            self.set_procash_header(worksheet)
            self.set_procash_lines_data(worksheet)
            xls_file_name = 'ProCash.xls'
        stream = BytesIO()
        workbook.save(stream)
        attach_id = self.env['bank.copy.print.link'].create(
            {
                'name': xls_file_name,
                'authority_xls_output': base64.b64encode(stream.getvalue())
            })
        return {
            # 'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'bank.copy.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class BankCopyPrintLink(models.TransientModel):
    _name = 'bank.copy.print.link'

    authority_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Bank Specific Report.xls')
