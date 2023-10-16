# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2018 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    categ_id = fields.Many2one('product.category', 'Internal Category',
                                required=True,default=False,
                                help="Select category for the current product")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=False)

    @api.multi
    def _action_confirm(self):
        ''' 
            Orverride sale Confirm Method to change confirmation date to Order Date
        '''
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            order.confirmation_date = order.date_order
        return res


class sale_order_line(models.Model):
    _inherit='sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        ''' 
            Orverride Sale Procurment Method to change date_planned to sale order Order Date
        '''
        res = super(sale_order_line, self)._prepare_procurement_values(group_id)
        res['date_planned'] = self.order_id.date_order
        return res


class stock_warehouse(models.Model):
    _name = "stock.warehouse"
    _inherit = ['stock.warehouse','mail.thread', 'mail.activity.mixin']

    name = fields.Char('Warehouse Name', index=True, required=True, 
                        default=lambda self: self.env['res.company']._company_default_get('stock.inventory').name,
                        track_visibility='onchange')
    active = fields.Boolean('Active', default=True,track_visibility='onchange')
    code = fields.Char('Short Name', required=True, size=5,
                        help="Short name used to identify your warehouse",
                        track_visibility='onchange')


class Location(models.Model):
    _name = "stock.location"
    _inherit = ['stock.location','mail.thread', 'mail.activity.mixin']

    name = fields.Char('Location Name', required=True, translate=True,track_visibility='onchange')
    active = fields.Boolean('Active', default=True,track_visibility='onchange',
              help="By unchecking the active field, you may hide a location without deleting it.")
    usage = fields.Selection([
        ('supplier', 'Vendor Location'),
        ('view', 'View'),
        ('internal', 'Internal Location'),
        ('customer', 'Customer Location'),
        ('inventory', 'Inventory Loss'),
        ('procurement', 'Procurement'),
        ('production', 'Production'),
        ('transit', 'Transit Location')], string='Location Type',
        default='internal', index=True, required=True,track_visibility='onchange',
        help="* Vendor Location: Virtual location representing the source location for products coming from your vendors"
             "\n* View: Virtual location used to create a hierarchical structures for your warehouse, aggregating its child locations ; can't directly contain products"
             "\n* Internal Location: Physical locations inside your own warehouses,"
             "\n* Customer Location: Virtual location representing the destination location for products sent to your customers"
             "\n* Inventory Loss: Virtual location serving as counterpart for inventory operations used to correct stock levels (Physical inventories)"
             "\n* Procurement: Virtual location serving as temporary counterpart for procurement operations when the source (vendor or production) is not known yet. This location should be empty when the procurement scheduler has finished running."
             "\n* Production: Virtual counterpart location for production operations: this location consumes the raw material and produces finished products"
             "\n* Transit Location: Counterpart location that should be used in inter-company or inter-warehouses operations")
    location_id = fields.Many2one(
        'stock.location', 'Parent Location', index=True, ondelete='cascade',track_visibility='onchange',
        help="The parent location that includes this location. Example : The 'Dispatch Zone' is the 'Gate 1' parent location.")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('stock.location'), index=True,
        help='Let this field empty if this location is shared between companies',track_visibility='onchange')


class PickingType(models.Model):
    _name = "stock.picking.type"
    _inherit = ['stock.picking.type','mail.thread', 'mail.activity.mixin']

    name = fields.Char('Operation Types Name', required=True, translate=True,track_visibility='onchange')
    code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')], 'Type of Operation', required=True,track_visibility='onchange')
    active = fields.Boolean('Active', default=True,track_visibility='onchange')


class ResUsers(models.Model):
    _inherit = "res.users"

    warehouse_ids = fields.Many2many(
        'stock.warehouse', string='Warehouse',
        help="User can see only configure warehouse records.")

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(ResUsers, self).create(vals)

    @api.multi
    def write(self, vals):
        self.clear_caches()
        return super(ResUsers, self).write(vals)

