import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from email.utils import getaddresses, formataddr

_logger = logging.getLogger(__name__)


class SaleOrderByCompany(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        comp_id = self.env.user.company_id.id
        try:
            if comp_id == 3:
                template_id = \
                    ir_model_data.get_object_reference('grimm_modifications', 'email_template_edi_sale_partenics')[1]
            else:
                template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            #'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'company_id': comp_id
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    # def action_cancel(self): #Removed web_notify dependency
    #     res = super(SaleOrderByCompany, self).action_cancel()
    #
    #     # Provided a message while cancelling if the purchase order exists and in draft or purchase state
    #     for rec in self:
    #         po = self.env['purchase.order'].search([('origin', '=', rec.name), ('state', 'in', ['draft', 'purchase'])])
    #         if po:
    #             self.env.user.notify_info(
    #                 _('Note: %s Purchase Order(s) exist(s) in draft and purchase state.' % len(po)))
    #     return res


class IrMailServerCompanies(models.Model):
    _inherit = 'ir.mail_server'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)


class SendMessageDialog(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        res = super(SendMessageDialog, self).default_get(fields)
        company_server_email = self.env['ir.mail_server'].sudo().search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)

        if 'email_from' in fields:
            res['email_from'] = company_server_email.smtp_user or self._get_default_from()
        if 'mail_server_id' in fields:
            res.update({'mail_server_id': company_server_email.id})
        return res


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def default_get(self, fields):
        result = super(MailMessage, self).default_get(fields)
        company_server_email = self.env['ir.mail_server'].sudo().search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        result.update({'mail_server_id': company_server_email.id})
        return result

    @api.model
    def _get_default_from(self):
        company_server_email = self.env['ir.mail_server'].sudo().search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        if self.env.user.email:
            return formataddr((self.env.user.name, company_server_email.smtp_user or self.env.user.email))
        raise UserError(_("Unable to send email, please configure the sender's email address."))
