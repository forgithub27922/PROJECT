# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class AssetAsset(models.Model):
    _inherit = 'grimm.asset.asset'

    def _get_history_contracts_count(self):
        for record in self:
            record.previous_contracts_count = self.env['sale.subscription'].sudo().search_count(
                [('asset_ids', 'in', record.id)])

    def _get_repair_count(self):
        for record in self:
            record.previous_repair_count = len(self.env['repair.order'].sudo().search(
                [('asset_id', '=', record.id)]))

    def _get_saleorder_count(self):
        for record in self:
            record.sale_order_count = self.env['sale.order'].sudo().search_count(
                [('asset_ids', 'in', record.id)])

    def _get_claim_count(self):
        for record in self:
            record.crm_claim_count = self.env['crm.claim'].search_count(
                [('asset_id', '=', record.id)])
            print(record.crm_claim_count)

    def _get_state(self):
        for record in self:
            if record.previous_contracts_count > 0:
                record.state = 'maintain'
            if record.previous_repair_count > 0:
                record.state = 'repair'
            else:
                record.state = 'none'

    def compute_age(self):
        if not self.manufacture_date:
            self.product_age = 'not set'
        else:
            now = fields.Date.from_string(fields.Date.today())
            man_date = fields.Date.from_string(self.manufacture_date)
            delta = now - man_date
            self.product_age = str(int(delta.days / 365.25)) + ' Jahr(e) ' + \
                               str(round(int(delta.days % 365.25) / 30.0, 1)) + ' Monat(e)'

    def compute_warranty(self):
        if self.placing_date and self.warranty:
            pl_date = fields.Date.from_string(self.placing_date)
            wa_date = pl_date + relativedelta(months=int(self.warranty))
            self.warranty_to = fields.Date.to_string(wa_date)
        else:
            self.warranty_to = ""

    previous_contracts_count = fields.Integer(
        string='Maintenance', compute=_get_history_contracts_count)
    previous_repair_count = fields.Integer(string='Repairs', compute=_get_repair_count)
    sale_order_count = fields.Integer(string='Sales Orders', compute=_get_saleorder_count)
    crm_claim_count = fields.Integer(string='Claims', compute=_get_claim_count)
    state = fields.Selection([
        ('none', '-'),
        ('repair', 'Repair'),
        ('maintain', 'Maintenance'),
        ('general', 'Miscellaneous'),
    ], default='none', compute=_get_state)
    warranty_type = fields.Many2one('product.warranty.type',
                                    string='Warranty Type', track_visibility='onchange')
    warranty = fields.Float(string="Warranty (months)", track_visibility='onchange')
    warranty_to = fields.Date(string="Warranty until", compute='compute_warranty')
    product_age = fields.Char(string='Age', compute='compute_age')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.warranty = self.product_id.warranty
        self.warranty_type = self.product_id.warranty_type
        return super(AssetAsset, self).onchange_product_id()
