from odoo import models, fields


class Updateage(models.TransientModel):
    _inherit = 'update.age.wizard'
    _desc = 'Inherit Update Age Wizard'

    mob_no = fields.Char('Mobile No')
    barcode = fields.Char('Barcode')

    def up_age(self):
        res = super().up_age()
        """
        this method will help for the update age from button
        :return:
        """
        customer_ids = self._context.get('active_ids')
        self.env[self._context.get('active_model')].browse(customer_ids).write(
            {'mob_no': self.mob_no, 'barcode': self.barcode})
        return res