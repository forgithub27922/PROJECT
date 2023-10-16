from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrKraConfiguration(models.Model):
    _name = "hr.kra.configuration"

    name = fields.Char(string="Name")
    line_ids = fields.One2many('hr.kra.configuration.line', "kra_id",
                               string="Lines")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('line_ids')
    def check_total_weightage(self):
        for rec in self:
            total = 0.0
            for data in rec.line_ids:
                if data.weightage:
                    total += data.weightage
            if total != 100.0:
                raise ValidationError('Total Weightage should be 100.')


class HrKraConfigurationLine(models.Model):
    _name = "hr.kra.configuration.line"

    question = fields.Text(string="Key Indicators")
    description = fields.Text(string="Description")
    weightage = fields.Float(string="Weightage")
    measurement_ids = fields.Many2many(
        'appraisal.measurement', 'rel_kra_conf_mea', 'kra_conf_id',
        'measurement_id', string="Measurement")
    kra_id = fields.Many2one("hr.kra.configuration", "KRA", ondelete='cascade')


class HrJob(models.Model):
    _inherit = "hr.job"

    hr_kra_id = fields.Many2one(comodel_name="hr.kra.configuration",
                                string="KRA")
