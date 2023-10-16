from odoo import models, fields


class Newprintcustomerreport(models.TransientModel):
    _name = 'new.print.customer.report.wiz'
    _desc = 'Print Customer Report'

    # custom_id = fields.Many2one('customer.customer', 'Customer')
    room_id = fields.Many2one('customer.room', string='Booking Rooms')
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string='Gender',
                              help='Gender selection field')
    company_id = fields.Many2one('res.company', 'COMPANY', default=lambda self: self.env.company.id)
    # user_id = fields.Many2one('res.users', 'User', company_dependent=True)

    def new_customer_wizard_html(self):
        """
        This method will fetch the students of the standard and print their report
        --------------------------------------------------------------------------
        @param self: object pointer
        :return: Action of the Report
        """
        cust_obj = self.env['customer.customer']
        Customers = cust_obj.search([('room_id', '=', self.room_id.id)])
        data = {
            'ids': Customers.ids,
            'form': self.read()[0]
        }


        action_name_html = 'hotel_mangement_14.action_hotel_new_report_html'
        report_action_html = self.env.ref(action_name_html).report_action(Customers.ids, data=data)
        report_action_html.update({'close_on_report_download': True})
        return report_action_html


    def new_customer_wizard_pdf(self):
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

        action_name_pdf = 'hotel_mangement_14.action_hotel_new_report_pdf'
        report_action_pdf = self.env.ref(action_name_pdf).report_action(customers.ids, data=data)
        report_action_pdf.update({'close_on_report_download': True})
        return report_action_pdf
