# -*- coding: utf-8 -*-


from odoo import api, models, _


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    def print_claim_warranty(self):
        return self.env['report'].get_action(self, 'grimm_reports.report_claim_warranty')

    def send_claim_warranty(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        comp_id = self.env.user.company_id.id
        if comp_id == 3:
            template = self.env.ref('grimm_modifications.email_template_warranty_claim_partenics', False)
        else:
            template = self.env.ref('grimm_reports.email_template_warranty_claim_grimm', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='crm.claim',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            company_id=comp_id,
            #custom_layout="account.mail_template_data_notification_email_account_invoice",
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def print_damage_report(self):
        return self.env['report'].get_action(self, 'grimm_reports.report_damage_report')

    def send_damage_report(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        comp_id = self.env.user.company_id.id
        if comp_id == 3:
            template = self.env.ref('grimm_modifications.email_template_damage_report_partenics', False)
        else:
            template = self.env.ref('grimm_reports.email_template_damage_report_grimm', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='crm.claim',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            company_id=comp_id,
            #custom_layout="account.mail_template_data_notification_email_account_invoice",
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
