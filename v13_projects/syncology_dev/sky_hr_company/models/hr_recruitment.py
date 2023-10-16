from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    @api.constrains('company_id')
    def check_company_email(self):
        """
        Override This method will check school email is configure or not
        ----------------------------------------------------------------
        @param self: object pointer
        """
        for applicant in self:
            if not applicant.company_id.email:
                raise ValidationError(_('Please configure email in School!!!'))