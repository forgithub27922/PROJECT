from odoo import fields, models


class AppraisalMeasurement(models.Model):
    _name = "appraisal.measurement"

    name = fields.Char("Name")
    code = fields.Char("Code")
    description = fields.Text("Description")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
