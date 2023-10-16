from odoo import models, fields, api , tools


class CustomerAnalysis(models.Model):
    _name = 'new.customer.analysis.report'
    _description = 'Customer Analysis'

    _auto = False

    name = fields.Char('Customer Name')

    hotel_name = fields.Char('Hotel Name')
    gender = fields.Char('Gender')
    age = fields.Integer('Age')
    day = fields.Char('Day')
    date = fields.Date('Date')
    taxes = fields.Float('Taxes')

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""create or replace view new_customer_analysis_report as
        (
            select cuch.id,cust.name,cust.age,cust.hotel_name,cust.gender,
            cuch.day,cuch.date,cuch.taxes  
            from customer_customer cust , customer_charges cuch
            where cuch.customer_id = cust.id
        )
        """)
