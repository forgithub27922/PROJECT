from odoo import models, fields


class Roomamenities(models.Model):
    _name = 'room.amenities'
    # _inherits = {'customer.room': 'room_Amenities_id'}
    _rec_name = 'room_code'
    room_Amenities_id = fields.Many2one('customer.room', 'Room Amenities', delegate=True)
    # room_inside_services = fields.Selection(selection=
    #                                         ([('shampoo', 'Shampoo and conditioner'), ('face', 'Face soap'),
    #                                           ('toothbrushes', 'Toothbrushes'),
    #                                           ('razors', 'Razors'), ('shaving', 'Shaving foam')
    #                                           ]))

    room_inside_servicess = fields.Many2many('customer.room.products', string='Room Products')

    def name_get(self):
        """
        this method to get the display name
        :return: A list of tuple
        """
        # res = super(Roomamenities, self).name_get()
        cust_lst = []
        for cust in self:
            cust_str = ''
            if cust.room_code:
                cust_str += cust.room_code + '-'
            if cust.room_type:
                cust_str += cust.room_type
            else:
                cust_str += ''
            cust_lst.append((cust.id, cust_str))
        print("dsddsd")
        return cust_lst
