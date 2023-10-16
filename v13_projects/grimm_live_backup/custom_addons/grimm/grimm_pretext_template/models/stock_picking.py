# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    salutation_text_tmpl_id = fields.Many2one(string='Pre-Tex Delivery Note',
                                              comodel_name='grimm.pretext.template',
                                              domain=['|', ('model_id', '=', False),
                                                      ('model_id.model', '=', 'stock.picking')])
    salutation_text = fields.Html(string="Pre-Text Delivery Note")

    # set salutation text from template
    @api.onchange('salutation_text_tmpl_id')
    def _onchange_salutation_text_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_tmpl_id', 'salutation_text', self)
