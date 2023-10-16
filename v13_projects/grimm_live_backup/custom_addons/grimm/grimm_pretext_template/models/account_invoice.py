# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    salutation_text_tmpl_id = fields.Many2one(string='Pre-Tex Template Prepayment',
                                              comodel_name='grimm.pretext.template',
                                              domain=['|', ('model_id', '=', False),
                                                      ('model_id.model', '=', 'account.move')])
    salutation_text_val_tmpl_id = fields.Many2one(string='Pre-Tex Template Invoice',
                                                  comodel_name='grimm.pretext.template',
                                                  domain=['|', ('model_id', '=', False),
                                                          ('model_id.model', '=', 'account.move')])
    salutation_text_refund_tmpl_id = fields.Many2one(string='Pre-Tex Template Refund',
                                                     comodel_name='grimm.pretext.template',
                                                     domain=['|', ('model_id', '=', False),
                                                             ('model_id.model', '=', 'account.move')])
    salutation_text = fields.Html(string="Pre-Text Prepayment")
    salutation_text_val = fields.Html(string="Pre-Text Invoice")
    salutation_text_refund = fields.Html(string="Pre-Text Refund")

    # set salutation text from template
    @api.onchange('salutation_text_tmpl_id')
    def _onchange_salutation_text_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_tmpl_id', 'salutation_text', self)

    # set salutation text from template
    @api.onchange('salutation_text_val_tmpl_id')
    def _onchange_salutation_text_val_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_val_tmpl_id', 'salutation_text_val', self)

    # set salutation text from template
    @api.onchange('salutation_text_refund_tmpl_id')
    def _onchange_salutation_text_refund_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_refund_tmpl_id', 'salutation_text_refund', self)
