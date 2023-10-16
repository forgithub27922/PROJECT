from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError, UserError
from datetime import date
import PyPDF2
from tempfile import gettempdir


class Customer(models.Model):
    _name = 'customer.customer'
    _description = 'Customer'
    _table = 'customer_customer'
    _auto = True
    _order = 'sequence'
    _parent_name = 'parent_id'
    _parent_store = True
    _sql_constraints = [
        ('unique_hotel_name', 'unique(hotel_name)', 'The hotel name is must be unique '),
        ('unique_reservation_no_email', 'unique(reservation_no,email)',
         'The reservation no and email of the customer must be unique!'),
        ('check_age', 'check(age>10)', 'The customer must be at least 10+ :) '),
        ('check_mob', 'check(length(mob_no)=10)', 'The Mobile Number must be 10 digit'),

    ]
    name = fields.Char(string='Guest Name', help='This is the Name of Customer')
    age = fields.Integer('Age', help='This is the Age of Customer', group_operator='sum')
    # age = fields.Char('Age', help='This is the Age of Customer', company_dependent=True, group_operator='avg')
    fee = fields.Float('Fee', default=500)
    code_of_bt = fields.Char('BT Code')
    reservation_no = fields.Char('Reservation No')
    date_order = fields.Date('Date Ordered')
    hotel_name = fields.Char('Hotel Name', tracking=True)
    # code = fields.Char('CODE')
    mob_no = fields.Char('Mobile No')
    barcode = fields.Char('Barcode')
    time = fields.Float('Time')
    bill = fields.Float('Bill', group_operator='avg', company_dependent=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Monetary(currency_field='currency_id', string='Amount')
    term_and_condition = fields.Boolean('Terms And Condition', default=True, help='Term And Condition')
    active = fields.Boolean('Active', default=True)

    notes = fields.Text('Notes', help='This is a Notes')
    comments = fields.Html('Comments', help='Add a Comment')
    birthdate = fields.Date('Birthdate', Index=True, default=fields.date.today(),
                            help='This is the date of birth of Customer', requried=True)
    check_in = fields.Datetime('Check In Date', help='This is the check in date in a hotel of Customer')
    check_out = fields.Datetime('Check Out Date', help='This is the check out date in a hotel of Customer')
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string='Gender',
                              help='Gender selection field')

    reservation_line = fields.Text('Reservation Line')
    password = fields.Char('Password')
    email = fields.Char('Email')
    website = fields.Char('Website')

    ref = fields.Reference([('res.partner', 'Partner'), ('res.users', 'Users'), ('customer.customer', 'Customer')],
                           'Reference')

    # Binary Field
    file_name_cust = fields.Char('File Name')
    document = fields.Binary('Upload Your PhotoID', store=True)

    image = fields.Binary('Image')

    priority = fields.Selection([(str(element), str(element)) for element in range(6)], 'Priority')

    payment_type = fields.Selection(
        [('google_pay', 'G-Pay'), ('phone_pay', 'Phone-Pay'), ('paypal', 'PayPal'), ('amazon-pay', 'Amazon-Pay')],
        string='Payment-Type')

    room_id = fields.Many2one('customer.room', string='Booking Rooms', check_company=True)

    charges_ids = fields.One2many('customer.charges', 'customer_id', string='Customer Charges')

    food_ids = fields.Many2many('customer.food', string='Amenities', check_company=True)
    total_amenities = fields.Integer('Total Amenities', compute='_total_amenities')
    total_amenities_price = fields.Float('Total Amenities Price', compute='_total_amenities_price')
    # user Defined
    # food1_ids = fields.Many2many('customer.food', 'fd_cust_rel', 'customer_id', 'food_id', 'Food Orders')

    sub_total = fields.Float('Sub Total', store=True, compute='_sub_total')
    taxes = fields.Float('Taxes :', compute='_tax_total')

    total_service = fields.Float('Total Services Charges :', compute='_services_charges')
    percent = fields.Float('Average Of Taxes', compute='_percent_taxes')

    state = fields.Selection([('room_book', 'Room Book'),
                              ('waiting', 'Waiting'),
                              ('rejected', 'Rejected'),
                              ('left', 'Left'),
                              ('accepted', 'Accepted'),
                              ('check_in', 'Check In'),
                              ('lunch', 'Lunch'),
                              ('dinner', 'Dinner'),
                              ('check_out', 'Check Out')], 'State')

    cust_seq = fields.Char('Customer code')

    color = fields.Integer('Color Index')

    cust_num = fields.Char('Customer Num')

    user_id = fields.Many2one('res.users', 'User', company_dependent=True)

    property_customer_type = fields.Selection(
        [('check_in', 'Check In'), ('check_out', 'Check Out'), ('not_exist', 'Not Exist')], 'Customer Type',
        company_dependent=True)

    partner_id = fields.Many2one('res.partner', 'Partner', company_dependent=True)

    # setting fields

    # no_of_customer =  fields.Integer('Number Of Customers', related='company_id.no_of_customer', readonly=False)
    # customer_mob_no = fields.Char('Customer Mobile Number', related='company_id.customer_mob_no', readonly=False)
    # hotel_open = fields.Boolean('Hotel Open?', related='company_id.hotel_open', readonly=False)
    # amenities_availabel = fields.Selection([('yes', 'YES'), ('no', 'NO')], string='Amenities Availabel',
    #                                        related='company_id.amenities_availabel', readonly=False)

    @api.depends('food_ids')
    def _total_amenities(self):
        """
        this method show the count of the amenities.
        @:param self : object pointer.

        """
        for item in self:
            total = 0
            for e in item.food_ids:
                total += 1
            item.total_amenities = total

        # search_count = self.search_count(['food_ids', '=', id])
        # self.total_amenities = search_count

    @api.depends('food_ids')
    def _total_amenities_price(self):
        for cust in self:
            total_price = 0
            for ele in cust.food_ids:
                total_price += ele.price
            cust.total_amenities_price = total_price

    @api.depends('charges_ids')
    def _sub_total(self):
        for charge in self:
            price_op = 0.0
            for elee in charge.charges_ids:
                price_op += elee.total_charges_service
            charge.sub_total = price_op

    @api.depends('charges_ids')
    def _tax_total(self):
        for tax in self:
            texes = 0
            for totaltax in tax.charges_ids:
                texes += totaltax.taxes
            tax.taxes = texes

    @api.depends('charges_ids')
    def _services_charges(self):
        ser = 0.0
        for s in self:
            ser = s.sub_total + (s.sub_total * (s.taxes / 100))
        s.total_service = ser

    @api.depends('taxes')
    def _percent_taxes(self):
        for tax in self:
            if len(tax.charges_ids) > 1:
                tax.percent = tax.taxes / len(tax.charges_ids)
            else:
                tax.percent = False

    # This method show the total of other charges and food charges
    # def _total_oc_fc(self):
    #     """
    #     This Method Will Calculate the total of other charges and food charges
    #     ----------------------------------------------------------------------
    #      @:param self : object pointer
    #
    #     """
    #     for customer in self:
    #         total_charge_of_oc_and_fc = 0.0
    #         total_o_charges = 0.0
    #
    #         # total_charge_of_oc_and_fc += customer.total_charges + customer.final_charges
    #         #
    #         # # total_o_charges += (customer.total_charges * 100 / customer.total_o_oc_fc)
    #         # customer.total_o_oc_fc = total_charge_of_oc_and_fc
    #         #
    #         # customer.percent = total_o_charges
    #
    # # This method will calculate the total of all charges
    #
    # def _total_charges(self):
    #     """
    #     This method will calculate the total of all charges
    #     ---------------------------------------------------
    #     @:param self : object pointer
    #     """
    #     for cust in self:
    #         # print(self)
    #         total_charge_c = 0.0
    #
    #         final_charges_c = 0.0
    #         # for charges in cust.charges_ids:
    #         #     total_charge_c += charges.total_charges_service
    #         #     # final_charges_c += charges.final_charge
    #         #
    #         # cust.total_charges = total_charge_c
    #         # # cust.final_charges = final_charges_c
    #
    # # This method show the percent of the food charges
    #
    # def _per_food_charges(self):
    #
    #     """
    #     This method will calculate the percent of the food charges
    #     @:param self : object pointer
    #     """
    #     pass
    #     # for num in self:
    #     #     if num.total_o_oc_fc != 0.0:
    #     #         num.percent = (num.final_charges * 100) / num.total_o_oc_fc
    #     #     # per = 0.0
    #         # for percentage in num.charges_ids:
    #         #     per = (percentage.discount*100) / 3
    #         # num.percent = per

    sequence = fields.Integer('Sequence',)

    parent_id = fields.Many2one('customer.customer', 'Manager')
    child_ids = fields.One2many('customer.customer', 'parent_id', 'Guest name')
    parent_path = fields.Char('Parent Path', index=True)

    company_id = fields.Many2one('res.company', 'COMPANY', default=lambda self: self.env.company.id)

    def wait_booking(self):
        for cust in self:
            cust.state = 'waiting'

    def reject_booking(self):
        for cust in self:
            cust.state = 'rejected'
            email_template = self.env.ref('hotel_mangement_14.mail_template_reject_customer')
            email_template.send_mail(cust.id, force_send=True)

    def accept_booking(self):

        hr = self.env[
            'res.config.settings'
        ]
        hop = hr.hotel_open
        print("\n\n\n\n---------------->lllllllllllllllll", hop)

        print("all keys", (list(self.env.keys())))
        print("all Values", (list(self.env.values())))
        print("all items", (list(self.env.items())))

        print("User Language", self.env.lang)
        print("User Company", self.env.company.id)
        print("User", self.env.companies, type(self.env.companies))
        print("user context", self.env.context)

        print("Model Recordset", self.env.ref('hotel_mangement_14.view_customer_form'))

        print("User Name", self.env.user)
        print("current user without using the env parameter user", self._uid)
        # print("current user without using the env parameter user", self.env.uid)
        print('values of predefined', self.get_metadata())
        print("@@@@@@@@@@@@", self.create_uid)
        # print("t55555555555555", self.env.ref['customer.customer'].search([('id','=',self.create_uid)]))

        print("ARGSSSSSSSSSSS", self.env.args)

        print("GETTTTTTTTTTTTTTTTT", self.env.get('ir.ui.view'))

        # (Q-17) use filtered method of recordset
        cust = self.search([])
        print('Filter', cust)
        filter_male = cust.filtered(lambda r: r.gender == 'male')
        print("Male Record", filter_male)
        filter_female = cust.filtered(lambda r: r.gender == 'female')
        print("Female Record", filter_female)

        # (Q-18)use filtered method when field value is none
        filter_email = cust.filtered(lambda r: r.email == False)
        print("Email Record", filter_email)

        # (Q-19)
        name = cust.mapped(lambda r: (r.name))
        age = cust.mapped(lambda r: (r.age))
        print("%s-%s" % (name, age))
        combo = ''
        for item in range(len(name)):
            combo += (str(name[item]) + '-' + str(age[item]) + ',')
        print('\n combo----------------->', combo)
        # name_age = cust.mapped(lambda r: (r.name, r.age))
        # print("using Map joined Name-Age", name_age)

        # (Q-20)
        name = cust.mapped('name')
        print("Give Value of Specific Field", name)

        # (Q-21)
        sort_record = cust.sorted(lambda r: r.id, reverse=True)
        print("Sort The Record In Desc", sort_record)

        # (Q-22)
        cust_all = self.search([])
        cust_few = self.search([('id', 'in', [1, 2, 3, 4, 5])])
        cust_few2 = self.search([('id', 'in', [6, 7, 8, 9])])
        cust_many = self.search([('id', 'in', [1, 3, 4, 5, 6, 7, 8, 9])])

        print("ALL", cust_all)
        print("FEW", cust_few)
        print("MANY", cust_few2)
        print("FEW2", cust_many)

        # Checking subset of a recordset
        print("SUBSET", cust_all < cust_few)

        # Checking superset of a recordset
        print("SUPERSET", cust_all > cust_many)

        # Union operation between two recordsets
        un_studs = cust_few | cust_few2
        print("Union", un_studs)

        # Intersection operation between two recordsets
        in_studs = cust_few2 & cust_many
        print("Intersection", in_studs)

        # Difference operation between two recordsets
        diff_studs = cust_few - cust_few2
        print("Difference", diff_studs)

        for cust in self:
            cust.state = 'accepted'

    def left(self):
        code = self.env['ir.sequence'].next_by_code('customer.customer')
        self.code_of_bt = code

        for cust in self:
            cust.state = 'left'

    def checkin(self):
        for cust in self:
            cust.state = 'check_in'
        res = self.get_metadata()
        print("===============================", res)

    def checkout(self):
        for cust in self:
            cust.state = 'check_out'
            no_of_cust = self.env.company.no_of_customer
            print("--->", no_of_cust)
            hotel_open = self.env.company.hotel_open
            print("--->", hotel_open)

    def lunch(self):
        for cust in self:
            cust.state = 'lunch'

    def dinner(self):
        for cust in self:
            cust.state = 'dinner'

    def create_record(self):
        """
        This method use for the create a record
        @:param self : object_pointer

        """

        # For OWN EXE
        # cust_vals ={
        #  'name': 'PARTH BHATT KAUSHIKBHAI',
        #  'hotel_name': 'LILA',
        #  'age': 23,
        #  'gender': 'male',
        #  'room_id': 3,
        #  'charges_ids': [
        #      (0, 0, {
        #          'day': 'monday',
        #          'morning_breakfast': 250.0,
        #          'aft_lunch': 270.0,
        #          'night_dinner': 300.0,
        #          'other_charges': 500.0,
        #          'discount': 12
        #       }),
        #    ],
        #  'food_ids': [
        #      (4, 1), (4, 2),
        #      (6, 0, [4, 6, 8, 9, 10])
        #  ],
        # }
        # cust = self.create([cust_vals])
        # print(cust)
        #

        # FOR QUE
        cust_vals = {
            'hotel_name': 'Grand Mercure',
            'name': 'SUJAL OP',
            'age': 23,
            'gender': 'male',
            'birthdate': fields.Date.today(),
            'email': 'dklathiwala@123',
            # 'room_id': 'RIT567',
            'charges_ids': [
                (0, 0, {
                    'day': 'monday',
                    'morning_breakfast': 320.0,
                    'aft_lunch': 200.0,
                    'night_dinner': 210.0,
                    'other_charges': 450.0,
                    'discount': 10
                }),
                (0, 0, {
                    'day': 'tuesday',
                    'morning_breakfast': 310.0,
                    'aft_lunch': 410.0,
                    'night_dinner': 120.0,
                    'other_charges': 1000.0,
                    'discount': 20
                }),
            ]
        }

        guest = self.create(cust_vals)
        print("Guest", guest)

    def update_record(self):
        """
        This method will Update the record
        @:param self :object-pointer
        """

        # For OWN EXE
        # cust_vals = {
        #     'name': 'SAHIL TIRKAR',
        #     'hotel_name': 'LILA',
        #     'age': 22,
        #     'gender': 'male',
        #     'room_id': 3,
        #     'charges_ids' :[
        #         (1,22,{
        #             'morning_breakfast' : 2500,
        #             'aft_lunch' : 2300,
        #             'night_dinner': 2000,
        #             'other_charges' : 4000
        #         })
        #     ],
        #     'food_ids': [
        #         (6, 0, [11, 9])
        #     ]
        #
        # }
        # self.write(cust_vals)
        #

        # FOR QUE
        cust_vals = {
            # 'hotel_name': 'Grand Mercure',
            # 'name': 'MANU OP',
            'age': 24,
            # 'gender': 'male',
            # 'birthdate': fields.Date.today(),
            # 'email': 'manuop@123',
            # 'room_id': 2,
            'charges_ids': [
                (1, 39, {
                    'taxes': 26.0
                })
                #   (1, 2, {
                #       'morning_breakfast': 250.0,
                #       'aft_lunch': 170.0
                #   })
                # Q-27 not remove it from the database.(3,3)
                # Q-28 remove it from the database. (2,3)
                #     (3, 19)
                #     (2, 19)
                # ],
                # 'food_ids': [
                #     # (4,7),(4,8),(4,9),(4,10)
                #     (6, 0, [11])
            ]

        }
        self.write(cust_vals)

    def browse_record(self):

        """
        this method will help browse the data.it is use for return record set of given id and ids
        @:param self : object pointer
        """

        # recordset of id
        customer = self.browse(25)
        print("Browse The Record", customer)
        # recordset of ids
        cust = self.search([])
        print("allllll", cust)
        cust.write({
            'age': 25
        })

        customers = self.browse([1, 4])
        print("CUSTOMERS BROWSEEEEEEE", customers)

        # customers.write({
        #     'age': 70
        # })

    def read_record(self):
        """
        This method will help the read record,its return a list of dict of the current record
        @:param self,field,load.
        """
        # dict = self.read()
        # print('\n\n\n\nRead Record', dict)

        # LOAD TYPE :- if we no show a load or load ='_classic_read' then it show a id and rec name of many 2 one fields.
        # if load="" then it show only id
        dict_specific = self.read(fields=['name', 'age', 'room_id', 'gender'], load="")
        print("\n\n\nSpecific Record", dict_specific)

        # for foreign record we have to make env then browse and then read
        room_obj = self.env['customer.room']
        print("room data", room_obj)
        res = room_obj.browse([1, 2, 3])
        print("Browse Data", res)
        room_rec = res.read()
        print("foreign record", room_rec)

    def copy_record(self):
        """
        this method will help for the copy of the record.
        @:param self : object pointer
        """
        name = self.name + ' (copy of this)'
        # cust = self.search([])
        # print("allllllsasssasasascopyyyyyyyyy", cust)
        dupl = self.copy(default={'name': name})
        print("copy", dupl)

    def delink_record(self):
        self.unlink()
        # delink for delete the currernt record

    def search_record(self):
        # it show a recordset of record
        customer = self.search([])
        print("All Customers", customer)

        # it show a recordset of male record
        male_cust = self.search([('gender', '=', 'male')])
        print("Male Customer", male_cust)

        # it is show a recordset by skipping(offset)2 record , limit 5 and order by id but in desc order
        order_by = self.search([], offset=2, limit=5, order='id desc')
        print("using another pra of search", order_by)

        count = self.search([], count=True)
        print("\n\n\ncount change the return type", count)

        search_count = self.search_count([])
        print("\n\n\n\nSearch Count Method", search_count)

        # child_cust = self.search([('i', 'child_of', [2])])
        # print("parent of ", child_cust)
        # for QUE
        # cl = self.search([])
        # print("All Records", cl)
        # customer = self.search([], offset=2, order='name')
        # print("ALL Customers", customer)
        # print("\n\n\n")
        # cust_op = self.search([], offset=5, count=True)
        # print("Count With Serach", cust_op)
        # cust_op2 = self.search_count([])
        # print("\n\n\n")
        # print("with search_count", cust_op2)

    def search_read_record(self):
        customer = self.search_read(domain=[], fields=['name', 'age'], offset=1, limit=5, order='id desc')
        print("\n\n\nsearch read method", customer)

        # # cu = self.search_read()
        # # print("cxxcxcc",cu)
        #
        #
        # customer_rec = self.search_read(domain=[('gender', '=', 'female')], fields=['name', 'gender', 'age'], offset=0)
        # print("All Record By Search read", customer_rec)
        #
        # # res = self.read_group([], fields=['name', 'gender', 'age'], groupby=['gender'])
        # # print(res)

    def read_group_record(self):
        cust_read_grp = self.read_group([], fields=['name', 'age'], groupby=['gender', 'state'], lazy=True)
        print("\n\n\nRECORD OF READ GROUP", cust_read_grp)

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create() method to set the sequence on the customer
        -------------------------------------------------------------
        :param vals_lst: A list of dictionary containing fields and values
        :return: A newly created recordset.
        """
        # print("values", vals_lst)
        # vals_lst = {
        #     'hotel_name': 'wwwwwkkkk',
        #     'name': 'Scout',
        #     'age': 22,
        #     'gender': 'male',
        #     'birthdate': fields.Date.today(),
        #     'email': 'scout@123',
        # }
        seq_u = self.env.ref('hotel_mangement_14.sequence_customer')
        for vals in vals_lst:
            vals.update({
                'cust_seq': seq_u.next_by_id()
            })
        return super().create(vals_lst)

    # def write(self, vals):
    #     for cust in self:
    #         if vals.get('fee', 0.0):
    #             vals['bill'] = vals['fee'] * 12
    #         else:
    #             vals['bill'] = cust.fee * 12
    #     return super().write(vals)

    # default get method of the main py file
    @api.model
    def default_get(self, fields_list):
        cust = super().default_get(fields_list)
        cust.update({
            'payment_type': 'phone_pay',
            'bill': cust.get('fee', 0.0) * 12,
            # NOT Allowed
            # 'cust_seq': self.env['ir.sequence'].next_by_code('customer.customer')
        })
        return cust

    @api.onchange('age', 'gender')
    def onchange_gender(self):
        """
        This method will change the fee based on the gender
        ---------------------------------------------------
        @param self: object pointer
        """

        for customer in self:

            if customer.gender == 'male':

                if customer.age <= 18:
                    customer.amount = 200.0
                    customer.bill = 200.0 + 200.0
                elif customer.age > 18:
                    customer.amount = 500.0
                    customer.bill = 500.0 + 300.0

            if customer.gender == 'female':

                if customer.age <= 18:
                    customer.amount = 100.0
                    customer.bill = 100.0 + 200.0
                elif customer.age > 18:
                    customer.amount = 400.0
                    customer.bill = 400.0 + 300.0




    # @api.onchange('gender', 'room_id', 'food_ids')
    # def onchange_gender(self):
    #     """
    #     This method will change the fee based on the gender
    #     ---------------------------------------------------
    #     @param self: object pointer
    #     """
    #     # students = self.search([('gender', '=', 'male')])
    #     # for cust in self:
    #     #     if students == True:
    #     #         cust.room_id = 1
    #     #         cust.food_ids = 12, 13
    #     #
    #     # cust = self.search([('gender', '=', 'female')])
    #     # for cust1 in self:
    #     #     if cust == True:
    #     #         cust1.room_id = 1
    #     #         cust1.food_ids = 12








    @api.constrains('room_id')
    def check_customer_number(self):
        for cust in self:
            customer_check = self.env['ir.config_parameter'].get_param('customer.check.in')
            hotel_cust = self.search_count([('room_id', '=', cust.room_id.id)])
            if hotel_cust >= int(customer_check):
                raise ValidationError(
                    'The Customer capacity is reached.You can not have more than {0} customers in the hotel'.format(
                        str(customer_check))
                )

    @api.constrains('reservation_no')
    def check_reservation_no_limit(self):
        """
        This method checks the reservation num limit
        ------------------------------------------------
        @param self: object pointer
        """
        # for cust in self:
        #     if len(cust.reservation_no) != 4:
        #         raise ValidationError('The length of Reservation number must be four')
        if len(self.reservation_no) != 4:
            raise ValidationError('The length of Reservation number must be four')

    def action_charges(self):
        return {
            'name': 'Charges',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'customer.charges',
            'domain': [('customer_id', '=', self.id)]

        }

    def update_age(self):
        return {
            'name': 'Update AGE',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'update.age.wizard',
            'target': 'new',
        }

    def _create_amenities(self):
        """
        This Method will Help to create amenities
        :return:
        """
        print("ssss")
        ame_obj = self.env['customer.food']
        amenities = self.search([])
        ame_vals_lst = []
        ame_vals = {
            'name': 'gyms',
            'price': 300,

        }
        ame_vals_lst.append(ame_vals)
        amen = ame_obj.create(ame_vals_lst)
        print(amen)

    # on change method for use calculate age from birthdate
    @api.onchange('age', 'birthdate')
    def onchange_age(self):
        """
        This method will change the age based on the birthdate
        ---------------------------------------------------
        @param self: object pointer
        """
        for customer in self:
            # print("vvvvvvvvvvvvvvvv",customer.birthdate)
            if customer.birthdate:
                today = date.today()
                customer.age = today.year - customer.birthdate.year
                # (today.month, today.day) < (customer.birthdate.month, customer.birthdate.day))
                print('today year', today.year)
                print('cust birth year', customer.birthdate.year)
                print('minus', today.year - customer.birthdate.year)
                # print('ee', (today.month, today.day))
                # print('ttt', (customer.birthdate.month, customer.birthdate.day))
                # print('age', customer.age)
            else:
                customer.age = 0

