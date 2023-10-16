from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    inverse_rate = fields.Float(
        'Current Inverse Rate', digits=(12, 4),
        help='The rate of the currency from the currency of rate 1 (0 if no '
             'rate defined).'
    )

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.inverse_rate != 0.0:
            res['manual_currency_rate_active'] = True
            res['inverse_rate'] = self.inverse_rate
            res['manual_currency_rate'] = 1 / self.inverse_rate
        return res




