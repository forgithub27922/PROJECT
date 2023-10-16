from odoo import models, fields


class Displayroomwiz(models.TransientModel):
    _name = 'customer.room.wiz'
    _desc = 'Display Rooms Record'

    room_id = fields.Many2one('customer.room', 'Rooms Name')

    def display_room_record(self):
        return {
            'name': 'Rooms',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'customer.customer',
            'domain': [('room_id', '=', self.room_id.id)]
        }
