from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_leave_expiry_notification = fields.Boolean(
        string="Allow Leave Expiry Notifications",
        help="Enable this to allow leave expiry notification to employee "
             "before a month.")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            allow_leave_expiry_notification=ICPSudo.get_param(
                'allow_leave_expiry_notification'))
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("allow_leave_expiry_notification",
                          self.allow_leave_expiry_notification)
