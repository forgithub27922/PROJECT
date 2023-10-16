from odoo import models, fields


class Showm2orecord(models.TransientModel):
    _name = 'm2o.record.wiz'

    customer_id = fields.Many2one('customer.customer', 'Customers')
