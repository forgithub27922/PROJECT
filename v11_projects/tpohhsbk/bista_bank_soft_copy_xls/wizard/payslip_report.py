# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

import xlsxwriter
import base64
from odoo import fields, models, api,_

from tempfile import gettempdir
import base64, os

class PayslipData(models.TransientModel):
    _name = 'pay.slip.data'

    name = fields.Char('File Name')
    file_download = fields.Binary('File to Download')


class PayslipReportWizard(models.TransientModel):
    _name = 'payslip.report.wizard'


    @api.multi
    def generate_payslip(self):
        file_name = 'Salary Sheet Excel Report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + file_name)
        worksheet = workbook.add_worksheet("Salary Sheet Excel Report")
        format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        format.set_font_size(10)

        format.set_text_wrap()
        font_bold = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter'})
        font_bold.set_bold()
        font_bold.set_font_size(11)
        font_bold.set_text_wrap()
        actual_data_format = workbook.add_format({'bg_color': '#B8B8B8',
                                                  'align': 'center',
                                                  'valign': 'vcenter'})
        actual_data_format.set_bold()
        actual_data_format.set_font_size(11)

        actual_data_format.set_text_wrap()

        amount_data_format = workbook.add_format({'bg_color': '#B8B8B8',
                                                  'align': 'center',
                                                  'valign': 'vcenter'})
        amount_data_format.set_bold()
        amount_data_format.set_font_size(11)
        amount_data_format.set_text_wrap()

        worksheet.set_column('A:A', 6)
        worksheet.set_column('B:D', 18)
        worksheet.set_column('E:G', 12)
        worksheet.set_column('H:AT', 16)

        row = 0
        col = 1
        worksheet.write(row, col, 'COMPANY #', font_bold)
        worksheet.write(row, col + 1, self.env.user.company_id.name or '', format)
        worksheet.write(4, 0, 'Code', font_bold)
        worksheet.write(4, 1, 'Employee', font_bold)
        worksheet.write(4, 2, 'Designation', font_bold)
        worksheet.write(4, 3, 'Number', font_bold)
        worksheet.write(4, 4, 'Start Date', font_bold)
        worksheet.write(4, 5, 'End Date', font_bold)
        worksheet.write(4, 6, 'Worked Days', font_bold)
        
        if self._context.get('is_batch_payslip'):
            active_ids = self._context.get('active_ids')
            batch_payslips = self.env['hr.payslip.run'].browse(active_ids)
            sale_recs = batch_payslips.mapped('slip_ids')
        else:
            active_ids = self._context.get('active_ids')
            sale_recs = self.env['hr.payslip'].browse(active_ids)
        location_dict = {}
        rule_data_lst = []
        column_seq_list = []
        column_seq_dict = {}
        p_rows = 5
        x_rows = 5
        cols = 7
        sum_cols = 7
        sum_rows =  5 + len(sale_recs) + 3

        # Create a format to use in the merged range.
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'yellow'})

        salary_rules = sale_recs.mapped('details_by_salary_rule_category').filtered(lambda r: r.total != 0 ).mapped('salary_rule_id').sorted(key=lambda r: r.sequence)
        rule_data_lst = salary_rules.mapped('name')
        all_lines = sale_recs.mapped('details_by_salary_rule_category').filtered(lambda r: r.total != 0 )
#         else :
#             salary_rules = sale_recs.mapped('details_by_salary_rule_category').mapped('salary_rule_id').sorted(key=lambda r: r.sequence)
#             rule_data_lst = salary_rules.mapped('name')
        
        final_rules_list = self.env['hr.salary.rule']
        basic_rules = salary_rules.filtered(lambda r: r.category_id.code == 'BASIC')
        if basic_rules:
            final_rules_list += basic_rules
            sum_basics =sum(all_lines.filtered(lambda r: r.category_id.code == 'BASIC').mapped('total'))
            if len(basic_rules) > 1:
                worksheet.merge_range(sum_rows,sum_cols,sum_rows,sum_cols+len(basic_rules)-1, 'Basic Total', merge_format)
                worksheet.merge_range(sum_rows+1,sum_cols,sum_rows+1,sum_cols+len(basic_rules)-1, sum_basics, font_bold)
            else:
                worksheet.write(sum_rows,sum_cols, 'Basic Total',merge_format)
                worksheet.write(sum_rows+1,sum_cols,sum_basics,font_bold)
            sum_cols += len(basic_rules)
            
        allw_rules = salary_rules.filtered(lambda r: r.category_id.code == 'ALW' or r.category_id.code == 'OTH')
        allw_rules_headers = allw_rules.mapped('report_header_id')
        allw_col_diff = 0
        allw_head_count = 0
        for tm_head in allw_rules_headers:
            allw_col_diff += len(allw_rules.filtered(lambda r: r.report_header_id.id == tm_head.id))
            allw_head_count += 1
            
        if allw_rules:
            final_rules_list += allw_rules
            sum_allws =sum(all_lines.filtered(lambda r: r.category_id.code == 'ALW' or r.category_id.code == 'OTH').mapped('total'))
            allw_flag = (len(allw_rules)-allw_col_diff)+allw_head_count
            if len(allw_rules) > 1 and allw_flag > 1:
                worksheet.merge_range(sum_rows,sum_cols,sum_rows,sum_cols+allw_flag-1, 'Allowance Total', merge_format)
                worksheet.merge_range(sum_rows+1,sum_cols,sum_rows+1,sum_cols+allw_flag-1, sum_allws, font_bold)
            else:
                worksheet.write(sum_rows,sum_cols,'Allowance Total',merge_format)
                worksheet.write(sum_rows+1,sum_cols,sum_allws,font_bold)
#             sum_cols += len(allw_rules) + flag
            sum_cols += allw_flag   
            
        gross_rules = salary_rules.filtered(lambda r: r.category_id.code == 'GROSS')
        gross_rules_headers = gross_rules.mapped('report_header_id')
        gross_col_diff = 0
        gross_head_count = 0
        for tm_head in gross_rules_headers:
            gross_col_diff += len(gross_rules.filtered(lambda r: r.report_header_id.id == tm_head.id))
            gross_head_count += 1
            
        if gross_rules:
            final_rules_list += gross_rules
            sum_gross =sum(all_lines.filtered(lambda r: r.category_id.code == 'GROSS').mapped('total'))
            gross_flag = (len(gross_rules)-gross_col_diff)+gross_head_count
            if len(gross_rules) > 1 and gross_flag > 1:
                worksheet.merge_range(sum_rows,sum_cols,sum_rows,sum_cols+gross_flag-1, 'Gross Total',merge_format)
                worksheet.merge_range(sum_rows+1,sum_cols,sum_rows+1,sum_cols+gross_flag-1,sum_gross, font_bold)
            else:
                worksheet.write(sum_rows,sum_cols,'Gross Total',merge_format)
                worksheet.write(sum_rows+1,sum_cols,sum_gross,font_bold)
#             sum_cols += len(gross_rules)
            sum_cols += gross_flag
          
        ded_rules = salary_rules.filtered(lambda r: r.category_id.code == 'DED' or r.category_id.code == 'COMP')
        ded_rules_headers = ded_rules.mapped('report_header_id')
        ded_col_diff = 0
        ded_head_count = 0
        for tm_head in ded_rules_headers:
            ded_col_diff += len(ded_rules.filtered(lambda r: r.report_header_id.id == tm_head.id))
            ded_head_count += 1
            
        if ded_rules:
            final_rules_list += ded_rules
            sum_deds =sum(all_lines.filtered(lambda r: r.category_id.code == 'DED' or r.category_id.code == 'COMP').mapped('total'))
            ded_flag = (len(ded_rules)-ded_col_diff)+ded_head_count
            if len(ded_rules)>1 and ded_flag > 1:
                worksheet.merge_range(sum_rows,sum_cols,sum_rows,sum_cols+ded_flag-1, 'Deduction Total', merge_format)
                worksheet.merge_range(sum_rows+1,sum_cols,sum_rows+1,sum_cols+ded_flag-1,sum_deds, font_bold)
            else:
                worksheet.write(sum_rows,sum_cols,'Deduction Total',merge_format)
                worksheet.write(sum_rows+1,sum_cols,sum_deds,font_bold)
            sum_cols += ded_flag
            
        net_rules = salary_rules.filtered(lambda r: r.category_id.code == 'NET')
        if net_rules:
            final_rules_list += net_rules
            sum_nets =sum(all_lines.filtered(lambda r: r.category_id.code == 'NET').mapped('total'))
            if len(net_rules) > 1:
                worksheet.merge_range(sum_rows,sum_cols,sum_rows,sum_cols+len(net_rules)-1, 'Net Total', merge_format)
                worksheet.merge_range(sum_rows+1,sum_cols,sum_rows+1,sum_cols+len(net_rules)-1,sum_nets, font_bold)
            else :
                worksheet.write(sum_rows,sum_cols,'Net Total',merge_format)
                worksheet.write(sum_rows+1,sum_cols,sum_nets,font_bold)
            sum_cols += len(net_rules)
            
        
        temp_report_header_list = []
        for rule in final_rules_list:
            rule_header = rule.report_header_id or False
            
            if rule_header: 
                if rule_header not in temp_report_header_list:
                    worksheet.write(4, cols, rule_header.name,font_bold)
                    column_seq_list.append((rule_header.name,cols))
                    column_seq_dict[rule_header.name] = cols
                    temp_report_header_list.append(rule_header)
                    rule_data_lst.append(rule_header.name)
                    cols += 1
            else:
                worksheet.write(4, cols, rule.name,font_bold)
                column_seq_list.append((rule.name,cols))
                column_seq_dict[rule.name] = cols
                cols += 1

        rule_data_lst = list(set(rule_data_lst))
        group_by_column_total = {}
        for rec in sale_recs:
            total_work_days = rec.worked_days_line_ids.mapped('number_of_days')
            location_dict.update(
                {'emp_name': rec.employee_id.name,
                 'number': rec.number,
                 'date_from':rec.date_from,
                 'date_to' : rec.date_to,
                 'employee_code' : rec.employee_id.employee_code or "" ,
                 'designation' : rec.employee_id.sudo().job_id and rec.employee_id.sudo().job_id.name or "" ,
                 'total_work_days' : total_work_days and sum(total_work_days) or ""
                 })

            for loc_name in rule_data_lst:
                for pay_line in rec.details_by_salary_rule_category:
                    if pay_line.salary_rule_id.report_header_id:
                        continue    
                    if pay_line.salary_rule_id.name == loc_name:
                        location_dict[loc_name] = pay_line.total
                        break
                    
            rule_headers = rec.details_by_salary_rule_category.mapped('salary_rule_id').mapped('report_header_id')
            
            for head in rule_headers:
                total = sum(rec.details_by_salary_rule_category.filtered(lambda r: r.salary_rule_id.report_header_id.id == head.id ).mapped('total'))
                location_dict[head.name] = total

            cols = 0
            worksheet.write(p_rows, cols,(location_dict.get('employee_code' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('emp_name' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('designation' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('number' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('date_from' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('date_to' or '')))
            cols += 1
            worksheet.write(p_rows, cols,(location_dict.get('total_work_days' or '')))

            p_rows += 1

            for l_name in rule_data_lst:
                if l_name in location_dict.keys():
                    cols = column_seq_dict.get(l_name)
                    worksheet.write(x_rows, cols,
                                location_dict.get(l_name))

                    if l_name not in group_by_column_total:
                        group_by_column_total.update({l_name:location_dict.get(l_name)})
                    else:
                        group_by_column_total[l_name] += location_dict.get(l_name)

                    location_dict[l_name] = 0
                    cols += 1
            x_rows += 1

        worksheet.write(p_rows+1, 0,"Total")
        for l_name in rule_data_lst:
            if l_name in group_by_column_total.keys():
                cols = column_seq_dict.get(l_name)
                value = group_by_column_total.get(l_name)
                worksheet.write(p_rows + 1, cols, value)
                cols += 1

        worksheet.center_vertically()
        worksheet.center_horizontally()
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_zoom(100)
        worksheet.set_print_scale(100)
        # worksheet.print_area(0, 0, row, col)
        worksheet.fit_page = 1
        worksheet.fit_to_pages(1, 1)
        workbook.close()
        pro_file = base64.b64encode(open('/tmp/' + file_name, 'rb').read())
        pro_cost_rec = self.env['pay.slip.data'].create(
            {'name': file_name, 'file_download': pro_file})
        return {
            'res_id': pro_cost_rec.id,
            'name': 'Files to Download',
            'view_type': 'form',
            "view_mode": 'form,tree',
            'res_model': 'pay.slip.data',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
