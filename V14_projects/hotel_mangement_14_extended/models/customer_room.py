from odoo import models, fields, api


class Room(models.Model):
    _name = 'customer.roomno'
    # _inherit = 'customer.room'

    check_in = fields.Date('Check In')
    check_out = fields.Date('Check Out')
    description = fields.Char('Description')
    duration = fields.Float("Duration in Days")
    unit_price = fields.Float("Unit Price")
    taxes = fields.Float("Taxes")
    # room_name = fields.Many2one('', 'Room Name')
    room_Ame_id = fields.Many2one('room.amenities', 'Rooms')

    cust_id = fields.Many2one('customer.customer', 'Customer Id')

    amount_room = fields.Float('Amount', compute='_total_amount_room')

    @api.depends('unit_price', 'taxes')
    def _total_amount_room(self):
        amount = 0.0
        for cust in self:
            print(">>>>>>>>>>", cust.unit_price, cust.taxes)
            amount = cust.unit_price + (cust.unit_price * (cust.taxes / 100))
            cust.amount_room = amount
