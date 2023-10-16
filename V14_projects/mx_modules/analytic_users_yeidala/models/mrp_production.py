# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.depends('picking_type_id', 'name')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            rec.account_analytic_id = self.env.user.account_analytic_id

    account_analytic_id = fields.Many2one('account.analytic.account', store=True, string='Analytic Account', compute='_compute_analytic_id_and_tag_ids', readonly=False)

    @api.model
    def _get_default_picking_type(self):
        account_analytic_id = self.env.user.account_analytic_id.id
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', '=', company_id), 
            ('warehouse_id.account_analytic_id', '=', account_analytic_id),
        ], limit=1).id

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        default=_get_default_picking_type, required=True, check_company=True)
    # , ('warehouse_id.account_analytic_id', 'in', user_account_analytic_ids)

    def write(self, vals):
        location = self.env.ref('stock.stock_location_stock')
        if 'picking_type_id' in vals:
            picking_type_id = self.env['stock.picking.type'].browse( vals['picking_type_id'] )
            vals['location_src_id'] = picking_type_id.default_location_src_id.id or location.id
            vals['location_dest_id'] = picking_type_id.default_location_dest_id.id or location.id
        res = super(MrpProduction, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        location = self.env.ref('stock.stock_location_stock')
        if 'picking_type_id' in vals:
            picking_type_id = self.env['stock.picking.type'].browse( vals['picking_type_id'] )
            vals['location_src_id'] = picking_type_id.default_location_src_id.id or location.id
            vals['location_dest_id'] = picking_type_id.default_location_dest_id.id or location.id
        production = super(MrpProduction, self).create(vals)
        return production
