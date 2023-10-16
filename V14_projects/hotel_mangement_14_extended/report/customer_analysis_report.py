from odoo import models, fields,api,tools


class Customerreport(models.Model):
    _inherit = 'new.customer.analysis.report'

    email = fields.Char('Email')
    payment_type = fields.Selection(
        [('google_pay', 'G-Pay'), ('phone_pay', 'Phone-Pay'), ('paypal', 'PayPal'), ('amazon-pay', 'Amazon-Pay')],
        string='Payment-Type')

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""create or replace view new_customer_analysis_report as
            (
            select cuch.id,cust.name,cust.age,cust.hotel_name,cust.gender,
            cuch.day,cuch.date,cuch.taxes,cust.email,cust.payment_type
            from customer_customer cust , customer_charges cuch
            where cuch.customer_id = cust.id
            )
            """)
