from odoo import models, fields


class Department(models.Model):
    _inherit = 'hr.department'

    appraisal_enable = fields.Boolean('Appraisal')