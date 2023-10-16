from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Company Fields
    no_of_customer = fields.Integer('Number Of Customers', related='company_id.no_of_customer', readonly=False)
    customer_mob_no = fields.Char('Customer Mobile Number', related='company_id.customer_mob_no', readonly=False)
    hotel_open = fields.Boolean('Hotel Open?', related='company_id.hotel_open', readonly=False)
    amenities_availabel = fields.Selection([('yes', 'YES'), ('no', 'NO')], string='Amenities Availabel',
                                           related='company_id.amenities_availabel', readonly=False)

    # system para
    hotel_room_check = fields.Selection([('booked', 'Booked'), ('still_open', 'Still Open')],
                                        string='Hotel Room Checking', config_parameter='hotel.room.check')
    customer_check = fields.Char('Customer ChecKing', config_parameter='customer.check.in')


    # groups
    group_hotel_admin = fields.Boolean('Admin Rights?', implied_group='hotel_mangement_14.grp_hotel_admin')
    group_hotel_14_user = fields.Boolean('User Rights?', implied_group='hotel_mangement_14.grp_hotel_14_user')

    # Module
    module_hotel_mangement_14_extended = fields.Boolean('Module Extended?')
