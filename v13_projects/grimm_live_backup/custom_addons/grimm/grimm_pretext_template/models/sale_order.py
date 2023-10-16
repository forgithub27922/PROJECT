# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    salutation_text_offer_tmpl_id = fields.Many2one(string='Template Pre-Text Offer',
                                                    comodel_name='grimm.pretext.template',
                                                    domain=['|', ('model_id', '=', False),
                                                            ('model_id.model', '=', 'sale.order')])
    salutation_text_offer = fields.Html(string="Pre-Text Offer")
    salutation_text_order_tmpl_id = fields.Many2one(string='Template Pre-Text Order',
                                                    comodel_name='grimm.pretext.template',
                                                    domain=['|', ('model_id', '=', False),
                                                            ('model_id.model', '=', 'sale.order')])
    salutation_text_order = fields.Html(string="Pre-Text Order")
    salutation_text_dn_tmpl_id = fields.Many2one(string='Template Pre-Text Delivery Note',
                                                 comodel_name='grimm.pretext.template',
                                                 domain=['|', ('model_id', '=', False),
                                                         ('model_id.model', '=', 'sale.order')])
    salutation_text_dn = fields.Html(string="Pre-Text Delivery Note")

    @api.model
    def update_salutation_text(self, template_field_name, text_field_name, records):
        for record in records:
            template = getattr(record, template_field_name, None)
            if not template:
                continue
            text = template.render_template(template.text, record)
            setattr(record, text_field_name, text)

    # set salutation text from template
    @api.onchange('salutation_text_offer_tmpl_id')
    def _onchange_salutation_text_offer_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_offer_tmpl_id', 'salutation_text_offer', self)

    # set salutation text from template
    @api.onchange('salutation_text_order_tmpl_id')
    def _onchange_salutation_text_order_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_order_tmpl_id', 'salutation_text_order', self)

    # set salutation text from template
    @api.onchange('salutation_text_dn_tmpl_id')
    def _onchange_salutation_text_dn_tmpl(self):
        self.env['sale.order'].update_salutation_text('salutation_text_dn_tmpl_id', 'salutation_text_dn', self)
