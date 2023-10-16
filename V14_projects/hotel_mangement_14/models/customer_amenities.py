from odoo import models, fields


class Food(models.Model):
    _name = 'customer.food'
    _description = 'Amenities'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Selection(selection=([
        ('toiletries', 'Toiletries (e.g. Shampoo, lotion, etc.)'),
        ('personalcare', 'Personal care (combs, shaving cream, razor, shower cap, hair dryer)'),
        ('coffeekit', 'Coffee Kit (maker, coffee and creamer)'),
        ('tissuebox', 'Tissue box'),
        ('bathrobes', 'Bathrobes and slippers'),
        ('wifi', 'Free WiFi internet access'),
        ('gyms', 'Gym or fitness center'),
        ('rollaway', ' Rollaway Tent'),
        ('powerbank', 'Powerbank for the Road'),
        ('room_pure', 'Room Purification'),
        ('local_history', ' Local History at Turndown'),
        ('premium_coffee', 'Premium Coffee'),

    ]), string='Amenities', tracking=True)
    price = fields.Integer('Price', tracking=True)
    color = fields.Integer('Color Index', tracking=True)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
