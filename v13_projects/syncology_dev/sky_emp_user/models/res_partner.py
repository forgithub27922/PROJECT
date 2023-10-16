from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_employee = fields.Boolean('Is Employee')

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if self._context.get('create_user') and self._context.get('no_reset_password'):
            res.is_employee = True
        return res
