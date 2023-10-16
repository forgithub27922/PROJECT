from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    appraisal_enable = fields.Boolean('Appraisal Enabled?', related='department_id.appraisal_enable')

