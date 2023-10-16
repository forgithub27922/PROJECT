# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    salutation_text_tmpl_id = fields.Many2one(string='Template Pre-Text Price Inquiry',
                                              comodel_name='grimm.pretext.template',
                                              domain=['|', ('model_id', '=', False),
                                                      ('model_id.model', '=', 'purchase.order')])
    salutation_text = fields.Html(string="Pre-Text Price Inquiry")
    salutation_text_po_tmpl_id = fields.Many2one(string='Template Pre-Text Purchase Order',
                                                 comodel_name='grimm.pretext.template',
                                                 domain=['|', ('model_id', '=', False),
                                                         ('model_id.model', '=', 'purchase.order')])
    salutation_text_po = fields.Html(string="Pre-Text Purchase Order")

    # set salutation text from template
    @api.onchange('salutation_text_tmpl_id')
    def _onchange_salutation_text_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_tmpl_id', 'salutation_text', self)

    # set salutation text from template
    @api.onchange('salutation_text_po_tmpl_id')
    def _onchange_salutation_text_po_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_po_tmpl_id', 'salutation_text_po', self)
