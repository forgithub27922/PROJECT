from odoo import models, fields, api
import datetime
import calendar

class Charges(models.Model):
        _name = 'customer.charges'

        _description = 'Charges'

        _rec_name = 'date'

        # day = fields.Selection(selection=[('monday', 'Monday'),
        #                                   ('tuesday', 'Tuesday'),
        #                                   ('wednesday', 'Wednesday')], string='Days', style='width:10%')
        day = fields.Char('Day', compute="_current_day",store=True)
        date = fields.Date("Date")
        service_ids = fields.Many2many('customer.service', string="Customer Services")
        taxes = fields.Float('Taxes')
        total_charges_service = fields.Float("Services Charges", compute='_total_services')
        # morning_breakfast = fields.Float('Breakfast')
        # aft_lunch = fields.Float('Lunch')
        # night_dinner = fields.Float('Dinner')
        # other_charges = fields.Float('Other Charges')
        # total_food_charges = fields.Float('Total Food Charges', compute='_total_food_charges')
        # discount = fields.Float('Discount Percent')
        # final_charge = fields.Float('Final Charge', compute='_percent_charges')


        # avg_charges = fields.Float('Average Charges', compute='_total_charges')
        customer_id = fields.Many2one('customer.customer', 'Customer')



        @api.depends('service_ids')
        def _total_services(self):
                for charges in self:
                        charge = 0.0
                        for price_all in charges.service_ids:
                                charge += price_all.price
                        charges.total_charges_service = charge

        @api.depends('date')
        def _current_day(self):
                for dates in self:
                        ans = False
                        if dates.date:
                                ans = dates.date.strftime("%A")
                        dates.day = ans



                        # x = datetime.date(sdate)
                        # ans = x.strftime("%A")
                        # self.day = ans


        # @api.depends('total_food_charges', 'morning_breakfast', 'aft_lunch', 'night_dinner')
        # def _total_food_charges(self):
        #         """
        #         This method will compute the food charges
        #         -----------------------------------------
        #         @:param self : object pointer
        #
        #         """
        #
        #         for custcharge in self:
        #             custcharge.total_food_charges = custcharge.morning_breakfast + custcharge.aft_lunch + custcharge.night_dinner

        # @api.depends('final_charge', 'total_food_charges', 'discount')
        # def _percent_charges(self):
        #         """
        #          this method will calculate percent of the charges
        #          ------------------------------------------------
        #          @:param self : object pointer
        #         """
        #         for perc in self:
        #                 perc.final_charge = (perc.total_food_charges)-((perc.total_food_charges / 100) * (perc.discount))
        #
