from odoo import models, fields


class EmailTempwiz(models.TransientModel):
    _name = 'email.temp.print.wiz'
    _desc = 'Print Email Template'

    customer_id = fields.Many2one('customer.customer', 'Customer')

    def print_email(self):
        if self.customer_id:
            email_templates = self.env.ref('hotel_mangement_14.wizard_email_template_customer')
            email_templates.send_mail(self.customer_id.id, force_send=True)