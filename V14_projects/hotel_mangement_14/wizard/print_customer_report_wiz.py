from odoo import models, fields, _, tools
import PyPDF2
from tempfile import gettempdir
import os
from pdf_layout_scanner import layout_scanner
import fitz


class Printcustomerreport(models.TransientModel):
    _name = 'print.customer.report.wiz'
    _desc = 'Print Customer Report'

    room_id = fields.Many2one('customer.room', string='Booking Rooms')

    def customer_wizard_html(self):
        """
        This method will fetch the students of the standard and print their report
        --------------------------------------------------------------------------
        @param self: object pointer
        :return: Action of the Report
        """
        cust_obj = self.env['customer.customer']
        customers = cust_obj.search([('room_id', '=', self.room_id.id)])
        data = {
            'ids': customers.ids,
            'form': self.read()[0]
        }

        action_name_html = 'hotel_mangement_14.action_hotel_report_html'
        report_action_html = self.env.ref(action_name_html).report_action(customers.ids, data=data)
        report_action_html.update({'close_on_report_download': True})
        return report_action_html

        # stud_obj = self.env['customer.customer']
        # students = stud_obj.search([('room_id', '=', self.room_id.id)])
        # data = {
        #     'ids': students.ids,
        #     'form': self.read()[0]
        # }
        #
        # action_name = 'hotel_mangement_14.action_hotel_report_html'
        # r_action = self.env.ref(action_name).report_action(students.ids, data=data)
        # r_action.update({'close_on_report_download': True})
        # return r_action

    def customer_wizard_pdf(self):
        """
        This method will fetch the students of the standard and print their report
        --------------------------------------------------------------------------
        @param self: object pointer
        :return: Action of the Report
        """
        cust_obj = self.env['customer.customer']
        customers = cust_obj.search([('room_id', '=', self.room_id.id)])
        data = {
            'ids': customers.ids,
            'form': self.read()[0]
        }

        action_name_pdf = 'hotel_mangement_14.action_hotel_report_pdf'
        report_action_pdf = self.env.ref(action_name_pdf).report_action(customers.ids, data=data)
        report_action_pdf.update({'close_on_report_download': True})
        return report_action_pdf

    # def read_pdf(self):
    #     # pdf_obj = open('/home/parth/Desktop/Customer.pdf', 'rb')
    #     # self.ensure_one()
    #     # for record in self:
    #     #     report_data = self.env['ir.actions.report'].search(
    #     #         [('report_name', '=', 'hotel_mangement_14.report_customer')])
    #     #     report_file_name = gettempdir() + "/" + tools.ustr(report_data.name) + '.pdf'
    #     #     print("----->", report_file_name)
    #     #     # data = report_data.render_qweb_pdf([record.id])[0]
    #     #     # print("--------------->", data)
    #     #     pdf1File = open(report_file_name, 'rb')
    #     #     pdf1Reader = PyPDF2.PdfFileReader(pdf1File)
    #     #     print("data", pdf1Reader)
    #     # # pdf_read = PyPDF2.PdfFileReader(pdf_obj)
    #     #     page_obj = pdf1Reader.getPage(0)
    #     #     print(page_obj.extractText())
    #     # # pdf_obj.close()
    #
    #     pdf_obj = open('/home/parth/Downloads/5168_Fee_Receipt.pdf', 'rb')
    #     pdf_read = PyPDF2.PdfFileReader(pdf_obj)
    #     # print(pdf_read.numPages)
    #     page_obj = pdf_read.getPage(0)
    #     print(page_obj.extractText())
    #     pdf_obj.close()
    #
    #
    # # def read_pdf(self):
    # #         pass
    # #             pdf_obj = self.customer_wizard_pdf()
    # #             pdf1File = open(pdf_obj, 'rb')
    # #             pdf1Reader = PyPDF2.PdfFileReader(pdf1File)
    # #             print(pdf1Reader)
    # #             print(pdf_obj.extractText())
    # #             # pdf_obj1 = PyPDF2.PdfFileReader(pdf_obj)
    # #             # self.ensure_one()
    # #             # for record in self:
    # #             #     report_data = self.env['ir.actions.report'].search(
    # #             #         [('report_name', '=', 'hotel_mangement_14.report_customer')])
    # #             #     print(report_data)
    # #             #     report_file_name = gettempdir() + "/" + tools.ustr(report_data.name) + '.pdf'
    # #             #     print(report_file_name)
    # #             #     data = report_data.render_qweb_pdf([record.id])[0]
    # #             #     f1 = open(os.path.join(report_file_name), 'wb+')
    # #             #     f1.write(data)
    # #             #     f1.close()
    # #             #     pdf1File = open(report_file_name, 'rb')
    # #             #     pdf1Reader = PyPDF2.PdfFileReader(pdf1File)
    # #             print(pdf1Reader)
    # #
    def read_pdf(self):
        import fitz

        # Path to input PDF
        pdf_path = '/home/parth/Downloads/school_14/Code Reference-20211018T131004Z-001/Code Reference/image_remove_pdf.pdf'

        # Open pdf
        doc = fitz.open(pdf_path)
        print("------>", doc)

        # Extract page
        page = doc[0]
        print("-------->", page)
