from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float('Discount Amount', store=True)
    disc_amt = fields.Float('Disc Amount')

    @api.onchange('discount', 'price_unit')
    def onchange_discount(self):
        for dis in self:
            print("TDDDDDD", dis.discount, dis.disc_amt, dis.price_unit)
            if dis.discount > 0.00:
                dis.disc_amt = (dis.price_unit * dis.discount) / 100.0

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        for vals in vals_list:
            if vals.get('discount', 0):
                vals.update({
                    'disc_amt': vals['price_unit'] * vals['discount'] / 100.0
                })
        return super(AccountMoveLine, self).create(vals_list)

    def write(self, vals):
        print("VALS", vals)
        for line in self:
            if vals.get('discount', 0):
                price_unit = vals.get('price_unit') and vals['price_unit'] or line.price_unit
                vals.update({
                    'disc_amt': price_unit * vals['discount'] / 100.0
                })
        return super().write(vals)

    # @api.depends('discount_amount', 'price_unit', 'discount')
    # def _cal_discount_amount(self):
    #     for amount in self:
    #         if amount.discount >= 1.00:
    #             amount.discount_amount = (amount.price_unit * amount.discount) / 100
