# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add a counter of failed email + configure
    the alias domain. """
    _inherit = 'res.config.settings'

    use_fixed_from_email = fields.Boolean(string="Use Fixed E-Mail Sender")
    fixed_from_email = fields.Char(string='Fixed E-Mail Sender')
    use_fixed_reply_to = fields.Boolean(string="Use Fixed E-Mail Reply To")
    fixed_reply_to_email = fields.Char(string='Fixed E-Mail Reply To')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        fixed_from_email = params.get_param("mail.fixed.sender", default=None)
        use_fixed_from_email = params.get_param("mail.use.fixed.sender", default=None)
        fixed_reply_to_email = params.get_param("mail.fixed.replyto", default=None)
        use_fixed_reply_to = params.get_param("mail.use.fixed.replyto", default=None)

        res.update(
            fixed_from_email=fixed_from_email or False,
            use_fixed_from_email=use_fixed_from_email or False,
            fixed_reply_to_email=fixed_reply_to_email or False,
            use_fixed_reply_to=use_fixed_reply_to or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        for record in self:
            params.set_param("mail.fixed.sender", record.fixed_from_email or '')
            params.set_param("mail.use.fixed.sender", record.use_fixed_from_email or '')
            params.set_param("mail.fixed.replyto", record.fixed_reply_to_email or '')
            params.set_param("mail.use.fixed.replyto", record.use_fixed_reply_to or '')
