from odoo import api, fields, models

class ActivateDeactivate(models.TransientModel):

    _name = "activate.deactivate.lms.wizard"
    _description = "Activate/deactivate LMS Wizard"

    company_id = fields.Many2one('res.company','company',default=lambda self: self.env.company)
    scheduler_active = fields.Boolean(related='company_id.scheduler_active')

    def activate(self):
        self.env.ref('sms_core.fee_detail_email').active = True
        self.company_id.scheduler_active = True

    def deactivate(self):
        self.env.ref('sms_core.fee_detail_email').active = False
        self.company_id.scheduler_active = False





