# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lapse_leaves = fields.Boolean(string="Lapse Leaves",
                                  related='company_id.lapse_leaves')


class ResCompany(models.Model):
    _inherit = 'res.company'

    lapse_leaves = fields.Boolean()
