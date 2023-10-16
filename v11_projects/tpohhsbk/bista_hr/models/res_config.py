
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_create_user = fields.Boolean(
        string="Is Create User",
        help="Enable this to create user while creating employee")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            is_create_user=ICPSudo.get_param('bista_hr.is_create_user'),
        )
        return res

    @api.multi
    def set_values(self):
        if self.is_create_user:
            self.onchanage_is_create_user()
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        ICPSudo.set_param("bista_hr.is_create_user", self.is_create_user)

    def onchanage_is_create_user(self):
        if self.is_create_user:
            employee_count = self.env['hr.employee'].search_count(
                [('user_id', '=', False)])
            if employee_count > 0:
                raise UserError("Please set related user in all\
                employee before Enable 'Create User' option")
