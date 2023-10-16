from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bank_soft_copy_amount_code = fields.Char(
        string="Bank Specific Report Code for Take Amount",
        help="Enable this to create user while creating employee")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            bank_soft_copy_amount_code=ICPSudo.get_param(
                'bank_soft_copy_amount_code'))
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "bank_soft_copy_amount_code", self.bank_soft_copy_amount_code)
