# -*- coding: utf-8 -*-

from odoo import models, fields


class IrModel(models.Model):
    _inherit = 'ir.model'

    grimm_text_tmpl_ids = fields.One2many(comodel_name='grimm.pretext.template', inverse_name='model_id')
