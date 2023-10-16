from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lm_csv_path = fields.Char('Laser Marker Path', related='company_id.lm_csv_path', readonly=False)