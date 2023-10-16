from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    
    @api.model
    def create(self,vals):
        print("\n\n\nM CALL:::::::::::-------------------------------->")
        ctx = self._context
        if ctx.get('payslip_id'):
            vals['name'] = ctx.get('payslip_id').move_name
        res = super(AccountMove,self).create(vals)
        return res