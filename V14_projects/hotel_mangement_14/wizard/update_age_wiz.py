from odoo import models, fields


class updateagewiz(models.TransientModel):
    _name = 'update.age.wiz'
    _desc = 'Update Age Wizard'

    custom_id = fields.Many2one('customer.customer', 'Customer')
    age = fields.Integer('Age', help='This is the Age of Customer')

    def update_age(self):
        """
        This method will help for the update age
        @:param self : object_pointer
        """

        if self.custom_id:
            self.custom_id.write({'age': self.age})
        else:
            custom_ids = self._context.get('active_ids')
            print("------------------>", custom_ids)
            self.env[self._context.get('active_model')].browse(custom_ids).write({'age': self.age})


    def update_custm_age(self):
        custm_ac_ids = self._context.get('active_ids')
        self.env[self._context.get('active_model')].browse(custm_ac_ids).write({'age': self.age})

    # def action_add_charges(self):
    #     return {
    #         'name':'Add Charges',
    #         'type':'ir.actions.act_window',
    #         'view_mode':'tree',
    #         'res_model':'customer.customer',
    #         'domain':[('','')]
    #
    #     }


class Updateage(models.TransientModel):
    _name = 'update.age.wizard'
    _desc = 'Update AGE'

    age = fields.Integer('Age', help='This is the Age of Customer')

    def up_age(self):
        """
        this method will help for the update age from button
        :return:
        """
        customer_ids = self._context.get('active_ids')
        self.env[self._context.get('active_model')].browse(customer_ids).write({'age': self.age})

