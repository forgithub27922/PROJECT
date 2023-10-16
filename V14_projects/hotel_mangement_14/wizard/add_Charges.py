from odoo import models, fields


class Addcharges(models.TransientModel):
    _name = 'add.charges.wiz'
    _desc = 'Add Charges Wizard'

    date = fields.Date("Date")
    service_ids = fields.Many2many('customer.service', string="Customer Services")
    taxes = fields.Float('Taxes')

    def add_charges(self):
        custom_ids = self._context.get('active_ids')
        obj = self.env[self._context.get('active_model')].browse(custom_ids)

        obj.write({'charges_ids': [(0, 0,
                                    {

                                        # 'day': self.day,
                                        'date': self.date,
                                        'service_ids': self.service_ids,
                                        'taxes': self.taxes,

                                    }

                                    )]})

    customer_id = fields.Many2one('customer.customer', 'Customer')

    def add_charges_id(self):
        # custom_ids = self._context.get('active_ids')
        obj = self.env['customer.customer'].browse(self.customer_id.id)
        obj.write({'charges_ids': [(0, 0,
                                    {
                                        'customer_id': self.customer_id,
                                        'date': self.date,
                                        'service_ids': self.service_ids,
                                        'taxes': self.taxes,

                                    }

                                    )]})
