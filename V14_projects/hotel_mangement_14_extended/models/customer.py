from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta


class Customer(models.Model):
    _inherit = ['customer.customer', 'mail.thread', 'mail.activity.mixin']
    _name = 'customer.customer'
    name = fields.Char(string='Guest Name', help='This is the Name of Customer', tracking=True)
    reservation_no = fields.Char('Reservation No', tracking=True)
    # q-4
    birthdate = fields.Date('Birthdate', required=True)
    comments = fields.Html('Comments', required=True)
    time = fields.Datetime('Time')

    room_num_ids = fields.One2many('customer.roomno', 'cust_id', string='Room No')
    notes = fields.Html('Notes')
    invoice_status = fields.Selection(selection=[('done', 'Done'), ('pending', 'Pending')], string="Invoice Status")
    like_hotel_service = fields.Selection(selection=[('yes', 'YES'), ('no', 'NO')],
                                          string="Would You like Hotel Services")
    address = fields.Char('Address')
    city_id = fields.Many2one('customer.city', 'City')

    cust_other_mob = fields.Char('Other Mobile NO')
    state = fields.Selection(selection_add=[
        ('nee_coffee', 'Need Coffee'),
        ('rejected', 'Rejected')], string='State')

    sub_unit_price = fields.Float('Sub Unit Price', compute='_sub_unit_price')

    @api.depends('room_num_ids')
    def _sub_unit_price(self):
        for unit_price in self:
            price = 0.0
            for sub_unit_price in unit_price.room_num_ids:
                price += sub_unit_price.unit_price
            unit_price.sub_unit_price = price

    # Q-5
    @api.onchange('age', 'gender', 'time', 'city_id')
    def onchange_gender(self):
        """
        This method will change the fee based on the gender
        ---------------------------------------------------
        @param self: object pointer
        """
        print("sssssssssss")
        result = super().onchange_gender()

        for changes in self.city_id:
            if changes.city == 'Ahmedabad':
                self.time = fields.Datetime.now()
                print("timeeeeeeeeeeeee", type(self.time), self.time)
                # self.time = current_time.strftime("%H:%M:%S:%p")
            elif changes.city == 'Tokyo':
                self.time = datetime.now()
            elif changes.city == 'New York City':
                a = datetime.now()
                b = timedelta(hours=9, minutes=30)
                self.time = a - b
                # = datetime.now() - datetime
        return result

    # Q-6
    @api.constrains('name')
    def check_reservation_no_limit(self):
        """
        This method checks the reservation num limit
        ------------------------------------------------
        @param self: object pointer
        """
        if len(self.cust_other_mob) < 10:
            raise ValidationError("The Mobile Number Must Be 10 Digits")

    # Q-7
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            'website': 'http://www.skyscendbs.com/',
            'like_hotel_service': 'yes'
        })
        return res

    def need_coffee(self):
        for custm in self:
            custm.state = 'nee_coffee'
