from odoo import models, fields, api, _


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    @api.onchange('company_id')
    def _get_mail_domain(self):
        if self.company_id.id == 1:
            self.alias_domain = self.env["ir.config_parameter"].get_param("mail.catchall.domain", default=None)
        else:
            self.alias_domain = self.env["ir.config_parameter"].get_param("mail.catchall.domain.partenics", default=None)
