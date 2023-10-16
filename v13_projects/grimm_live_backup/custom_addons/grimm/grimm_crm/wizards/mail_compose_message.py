# -*- coding: utf-8 -*-

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    is_notify_follower = fields.Boolean(string='Sent to followers', default=False, help='Notify to all on follower')

    # parent_reply_id = fields.Many2one('mail.message', 'Parent Reply Message', ondelete='set null')

    @api.model
    def default_get(self, fields):
        result = super(MailComposer, self).default_get(fields)

        # result['parent_reply_id'] = result.get('parent_reply_id', self._context.get('parent_reply_id'))

        return result

    @api.onchange('is_notify_follower')
    def onchange_is_notify_follower(self):
        if self.is_notify_follower:
            self.subtype_id = 1
        else:
            self.subtype_id = 2

    def send_mail_action(self):
        for wizard in self:
            if not wizard.is_notify_follower:
                if not wizard.partner_ids:
                    return ValidationError(_("E-Mail doesn't have any receiver"))
                self.is_log = True

        res = super(MailComposer, self).send_mail_action()
        return res

    @api.onchange('template_id')
    def onchange_template_id_wrapper(self):
        self.ensure_one()
        values = self.onchange_template_id(self.template_id.id, self.composition_mode, self.model, self.res_id)['value']
        object = self.env[self.model].sudo().browse(self.res_id)
        company_id = getattr(object, "company_id")
        IrMailServer = self.env['ir.mail_server']
        if self.template_id.mail_server_id:
            values["mail_server_id"] = self.template_id.mail_server_id.id
        elif company_id:
            company_mail_server = IrMailServer.sudo().search([('company_id', '=', company_id.id)],limit=1)
            if company_mail_server:
                values["mail_server_id"] = company_mail_server.id
        for fname, value in values.items():
            if self.template_id.not_overwrite:
                if fname == 'body':
                    value = value + self.body
                elif fname == 'attachment_ids':
                    if value:
                        tmp = value[0][2]
                        tmp.extend([attachment.id for attachment in self.attachment_ids])
            setattr(self, fname, value)
