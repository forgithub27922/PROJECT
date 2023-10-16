from odoo import models, fields, api


class Room(models.Model):
    _name = 'customer.room'
    _description = 'Room'
    _rec_name = 'room_code'

    room_code = fields.Char('Room Code', readonly=False)
    room_type = fields.Selection(selection=[('single', 'Single'),
                                            ('double', 'Double'),
                                            ('triple', 'Triple'),
                                            ('quad', 'Quad'),
                                            ('queen', 'Queen'),
                                            ('hollywood', 'Hollywood Twin Room'),
                                            ('double_double', 'Double-Double'),
                                            ('studio', 'Studio'),
                                            ('suite', 'Executive Suite'),
                                            ('junior', 'Junior Suite'),
                                            ('presidential', ' Presidential Suite'),
                                            ('apartments', 'Apartments'),
                                            ('connecting', 'Connecting rooms'),
                                            ('murphy', 'Murphy Room'),
                                            ('accessible', 'Accessible Room'),
                                            ('cabana', 'Cabana'),
                                            ('adjoining', 'Adjoining rooms'),
                                            ('villa', 'Villa'),
                                            ('double_open', 'Double Open'),
                                            ('squad_type', 'Squad'),
                                            ('duo_squad_type', 'Duo Squad')
                                            ],
                                 string='Room Type'
                                 )
    room_capacity = fields.Selection(selection=[('two_people', 'Two People'),
                                                ('three_people', 'Three People'),
                                                ('five_people', 'Five People'),
                                                ('six_people', 'Six People')],
                                     string='Room Capacity'
                                     )

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    def name_get(self):
        """
        this method to get the display name
        :return: A list of tuple
        """
        print("aaaaaaaaaaa")
        cust_lst = []
        for cust in self:
            cust_str = ''
            if cust.room_code:
                cust_str += cust.room_code + '-'
            print('string', cust_str)
            print('room', cust.room_type)
            if cust.room_type:
                cust_str += cust.room_type
            else:
                cust_str += ''
            cust_lst.append((cust.id, cust_str))
        print("cust_lst::::::::::", cust_lst)
        return cust_lst

    #
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        this method search the record from the m2o field
        :return: list of tuple
        """
        print("ssssssssss")
        if not args:
            args = []
        args += ['|', ('room_code', operator, name), ('room_type', operator, name)]
        rooms = self.search(args, limit=limit)
        return rooms.name_get()

    @api.model
    def name_create(self, name):
        print("fffffffffffff")
        if name:
            room = self.create(
                {
                    'room_code': name.upper(),
                    'room_type': 'deluxe',
                    'room_capacity': 'three_people',
                }
            )
        return room.name_get()[0]
