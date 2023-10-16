from odoo import models, fields, api
import xlsxwriter
import base64
import io


class CustomerXLSReportWizard(models.TransientModel):
    _inherit = 'customer.xls.report.wiz'


    def cust_print_xls_report(self):
        """
        This method will create an xls report
        -------------------------------------
        @param self: object pointer
        :return: XLS Report
        """
        attach_obj = self.env['ir.attachment']
        # Open Workbook
        wb = xlsxwriter.Workbook('/tmp/customer_report.xlsx')
        for customer in self.customer_ids:
            ws = wb.add_worksheet(customer.name)
            title_format = wb.add_format({'size': 20, 'bold': True, 'font_color': 'blue'})
            hdr_format = wb.add_format({'size': 14, 'bold': True, 'font_color': 'green'})
            bold_format = wb.add_format({'size': 11, 'bold': True, 'font_color': 'red'})
            ws.merge_range(2, 3, 4, 5, 'Customer Report', title_format)
            ws.write(8, 0, 'Name', hdr_format)
            ws.write(8, 1, customer.name)
            ws.write(9, 0, 'Gender', hdr_format)
            ws.write(9, 1, customer.gender)
            ws.write(9, 2, 'Age', hdr_format)
            ws.write(9, 3, customer.age)
            ws.write(9, 4, 'Hotel Name', hdr_format)
            ws.write(9, 5, customer.hotel_name)
            ws.write(9, 6, 'Customer Amount', hdr_format)
            ws.write(9, 7, customer.amount)
            # ws.write(10, 7, 'Customer Room', hdr_format)
            # ws.write(10, 8, customer.room_id.room_code)

            ws.write(0, 0, 'Customer Image', hdr_format)
            # ws.write(0, 0, customer.image)
            customer_img = customer.image
            if (customer_img):
                imgdata = base64.b64decode(customer_img)
                image = io.BytesIO(imgdata)
                ws.insert_image(0, 1, 'patient_image', {'image_data': image, 'x_scale': 0.1, 'y_scale': 0.1})

            row = 11
            ws.write(row, 0, 'Day')
            ws.write(row, 1, 'Date')
            ws.write(row, 2, 'Services')
            ws.write(row, 3, 'Taxes')
            ws.write(row, 4, 'services charges')
            ws.write(row, 6, 'Amount')


            row += 1
            charges_tax = 0.0
            total_ser = 0.0
            for charge in customer.charges_ids:
                ws.write(row, 0, charge.day)
                date = charge.date.strftime('%d-%m-%Y')
                # print("-------->", date)
                # print(s)
                ws.write(row, 1, date)
                for ch in charge.service_ids:
                    ws.write(row, 2, ch.name)
                ws.write(row, 3, charge.taxes)

                ws.write(row, 4, charge.total_charges_service)
                ws.write(row, 6, (charge.total_charges_service + ((charge.total_charges_service * charge.taxes) / 100)))
                row += 1




                # count of taxes and charges
                charges_tax += charge.taxes
                total_ser += charge.total_charges_service


            chart = wb.add_chart({'type': 'pie'})

            chart.add_series({
                'name': 'Customer Report',
                # 'categories': '=customer.name!$A$13:$A$17',
                # 'values': '=customer.name!$C$13:$C$17'
                'categories': [customer.name, 12, 2, row - 1, 2],
                'values': [customer.name, 12, 6, row - 1, 6]
            })

            chart.set_title({'name': 'Excel Report'})

            ws.insert_chart('M9', chart)

            ws.write(17, 3, charges_tax, bold_format)
            ws.write(17, 4, total_ser, bold_format)






        wb.close()
        f1 = open('/tmp/customer_report.xlsx', 'rb')
        xls_data = f1.read()
        buf = base64.encodestring(xls_data)
        doc = attach_obj.create({'name': '%s.xlsx' % ('Customer Report'),
                                 'datas': buf,
                                 'res_model': 'customer.xls.report.wiz',
                                 'store_fname': '%s.xlsx' % ('Customer Report'),
                                 })
        return {'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true' % (doc.id),
                'target': 'current',
                'close_on_report_download': True
                }
