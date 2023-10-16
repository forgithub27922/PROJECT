from odoo import models, fields


class Roomproduct(models.Model):
    _name = 'customer.room.products'
    _desc = 'Room Product'
    _rec_name = 'room_product'

    room_product = fields.Char('Room Products')
    product_code = fields.Char('Product Code')
