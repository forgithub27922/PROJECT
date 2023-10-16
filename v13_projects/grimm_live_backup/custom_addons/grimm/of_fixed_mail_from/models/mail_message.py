# -*- coding: utf-8 -*-


from odoo import api, fields, models, SUPERUSER_ID, tools, _
from email.utils import formataddr
from odoo.exceptions import UserError


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'

    @api.model
    def _get_default_from(self):
        params = self.env['ir.config_parameter'].sudo()
        use_fixed_from_email = params.get_param("mail.use.fixed.sender")
        if use_fixed_from_email:
            return params.get_param("mail.fixed.sender")
        if self.env.user.alias_name and self.env.user.alias_domain:
            return formataddr((self.env.user.name, '%s@%s' % (self.env.user.alias_name, self.env.user.alias_domain)))
        elif self.env.user.email:
            return formataddr((self.env.user.name, self.env.user.email))
        raise UserError(
            _("Unable to send email, please configure the sender's email address or alias."))

    @api.model
    def _get_reply_to(self, values):
        """ Return a specific reply_to for the document """
        params = self.env['ir.config_parameter'].sudo()
        use_fixed_reply_to = params.get_param("mail.use.fixed.replyto")
        if use_fixed_reply_to:
            return params.get_param("mail.fixed.replyto")
        model = values.get('model', self._context.get('default_model'))
        res_id = values.get('res_id', self._context.get('default_res_id'))
        email_from = values.get('email_from')
        message_type = values.get('message_type')
        records = None
        if self.is_thread_message({'model': model, 'res_id': res_id, 'message_type': message_type}):
            records = self.env[model].browse([res_id])
        else:
            res_id = False
        return self.env['mail.thread']._notify_get_reply_to_on_records(default=email_from, records=records)[res_id]


class MailComposeMessage(models.TransientModel):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.compose.message'

    @api.model
    def _get_default_from(self):
        params = self.env['ir.config_parameter'].sudo()
        use_fixed_from_email = params.get_param("mail.use.fixed.sender")
        if use_fixed_from_email:
            return params.get_param("mail.fixed.sender")
        if self.env.user.alias_name and self.env.user.alias_domain:
            return formataddr((self.env.user.name, '%s@%s' % (self.env.user.alias_name, self.env.user.alias_domain)))
        elif self.env.user.email:
            return formataddr((self.env.user.name, self.env.user.email))
        raise UserError(
            _("Unable to send email, please configure the sender's email address or alias."))

    @api.model
    def _get_reply_to(self, values):
        """ Return a specific reply_to for the document """
        params = self.env['ir.config_parameter'].sudo()
        use_fixed_reply_to = params.get_param("mail.use.fixed.replyto")
        if use_fixed_reply_to:
            return params.get_param("mail.fixed.replyto")
        model = values.get('model', self._context.get('default_model'))
        res_id = values.get('res_id', self._context.get('default_res_id'))
        email_from = values.get('email_from')
        message_type = values.get('message_type')
        records = None
        if self.is_thread_message({'model': model, 'res_id': res_id, 'message_type': message_type}):
            records = self.env[model].browse([res_id])
        else:
            res_id = False
        return self.env['mail.thread']._notify_get_reply_to_on_records(default=email_from, records=records)[res_id]

    @api.model
    def default_get(self, fields):
        res = super(MailComposeMessage, self).default_get(fields)
        if 'email_from' in fields:
            res['email_from'] = self._get_default_from()
        return res
