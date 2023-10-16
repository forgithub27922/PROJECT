from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        """
        This method is used to check the payment of the receipt
        -------------------------------------------------------
        :param self:  object pointer
        """
        res = super(AccountMove, self).write(vals)
        receipt_id = self.id
        if self._context.get('active_model') == 'account.move':
            receipt_id = self._context.get('active_id')
        if self.amount_residual == 0.0:
            for picking in self.env['stock.picking'].search([('receipt_id', '=', receipt_id)]):
                picking.payment_status = True
        return res