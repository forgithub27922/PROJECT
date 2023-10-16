from odoo import models, fields

class Service(models.Model):
    _name = 'customer.service'
    _description = 'Services'
    _table = 'customer_service'
    _auto = True

    # name = fields.Selection(selection=([
    #                                         ('roomservice', 'Room service (24-hour)'),
    #                                         ('carrental', 'Car rental services'),
    #                                         ('doctorcall', 'Doctor on call'),
    #                                         ('ironservices', 'Ironing service'),
    #                                         ('massages', 'Massages'),
    #                                         ('valet', 'Valet parking'),
    #                                         ('laundry', 'Laundry and valet service')
    #                                     ]), string='Services')
    name = fields.Char('Services Name :: ', required=True)
    price = fields.Float('Price', required=True)
    # category = fields.Char('Service Category')
    category = fields.Selection(selection=([
        ('all', 'All Services / Optional'),
        ('fixed', 'All Services / Fixed'),
    ]), string="Service Category")
    desc = fields.Text('Description', default= "Whether you are travelling for business or pleasure, the luxury hotel services offered by the five star Grand Palace Hotel make it an ideal choice for your stay in Riga, Latvia. The hotel’s luxurious surroundings, comfort, thoughtful touches and a personalized service sets it apart from any other hotel, "
                                               "allowing you to feel like being at home from your very first steps into the hotel")