# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class Partner(models.Model):
    _inherit = 'res.partner'

    property_supplier_pricelist = fields.Many2one(comodel_name='product.pricelist', string='Supplier Price List',
                                                  help='Price list to calculate the purchase price', copy=False,
                                                  track_visibility='onchange')

    purchase_pricelist_ids = fields.One2many(comodel_name="partner.pricelist.item", inverse_name="partner_id",
                                             string="Purchase Price List (IN)")
    apply_purchase_pricelist = fields.Boolean(string="Apply purchase price list",
                                              help="If you activate, odoo will override the price based on below rules.")
    sale_pricelist_ids = fields.One2many(comodel_name="partner.sale.pricelist.item", inverse_name="partner_id",
                                         string="Sale Price List (OUT)")
    apply_sale_pricelist = fields.Boolean(string="Apply Sales price list",
                                              help="If you activate, odoo will override the price based on below rules.")
    sale_base_price = fields.Selection(
        selection=[('calculated_standard_price', 'Purchase Price'),
                   ('rrp_price', 'List Price')],
        string='Based price',
        default='calculated_standard_price',
        help="Here you can select base price for calculation, for some product"
             " we want to calculate based on purchase price and for some product"
             " it calculated based on List price."
    )

    """
    property_supplier_pricelist_items = fields.One2many(comodel_name='product.pricelist.item',
                                                        inverse_name='supplier_id',
                                                        string='Supplier Price List Items',
                                                        help='Price list to calculate the purchase price', copy=False,
                                                        track_visibility='onchange')
    """

    @api.model
    def get_supplier_pricelist(self):
        if self.property_supplier_pricelist:
            return self, self.property_supplier_pricelist
        if self.parent_id:
            return self.parent_id.get_supplier_pricelist()
        return None




class PartnerPricelistItem(models.Model):
    _name = 'partner.pricelist.item'
    _description = 'Vendor Pricelist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, partner_id'


    sequence = fields.Integer(string="Sequence")
    name = fields.Char(string='Pricelist Name',track_visibility='onchange')
    compute_price = fields.Selection([
        ('fixed', 'Fix Price'),
        ('percentage', 'Percentage (discount)'),
        ('formula', 'Formula')], index=True, default='fixed', track_visibility='onchange')
    is_accessory_part = fields.Selection([
        ('y', 'Yes'),
        ('n', 'No'),
        ('-', '---')], index=True, default='-', track_visibility='onchange')
    is_spare_part = fields.Selection([
        ('y', 'Yes'),
        ('n', 'No'),
        ('-', '---')], index=True, default='-', track_visibility='onchange')
    is_device = fields.Selection([
        ('y', 'Yes'),
        ('n', 'No'),
        ('-', '---')], index=True, default='-', track_visibility='onchange')
    is_product_pack = fields.Selection([
        ('y', 'Yes'),
        ('n', 'No'),
        ('-', '---')], index=True, default='-', track_visibility='onchange')
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('0_product_variant', 'Product')], "Apply On",
        default='3_global', required=True,
        help='Pricelist Item applicable on selected option', track_visibility='onchange')

    base = fields.Selection([('rrp_price', 'List Price'),('list_price', 'Public Price'),('standard_price', 'Cost')], string="Based On", track_visibility='onchange')
    percent_sign = fields.Selection([('-', '-'), ('+', '+')], string='Percent Sign', default='-',required=True, track_visibility='onchange')



    min_uvp = fields.Float(name='Min. UVP', copy=True, default=0.00, track_visibility='onchange')
    product_net_weight = fields.Float(name='Net weight greater than',
                                      help="If product net weight is greater or equal to this value then rules will be applied.",
                                      track_visibility='onchange')
    product_name = fields.Char(string='Product Name contain', help='Product name contains this text',
                               track_visibility='onchange')
    product_brand_id = fields.Many2one('grimm.product.brand', string='Brand', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Supplier Id', track_visibility='onchange')

    price_calculation_group = fields.Many2one("product.price.group", string="Price Calculation Group", copy=True,
                                              track_visibility='onchange')
    attribute_set_id = fields.Many2one('product.attribute.set', string='Attribute set', copy=False,
                                       track_visibility='onchange')
    min_quantity = fields.Integer(
        'Min. Quantity', default=0,
        help="For the rule to apply, bought/sold quantity must be greater "
             "than or equal to the minimum quantity specified in this field.\n"
             "Expressed in the default unit of measure of the product.", track_visibility='onchange')

    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation",
                             track_visibility='onchange')
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation",
                           track_visibility='onchange')
    price_round = fields.Float(
        'Price Rounding', digits='Product Price',
        help="Sets the price so that it is a multiple of this value.\n"
             "Rounding is applied after the discount and before the surcharge.\n"
             "To have prices that end in 9.99, set rounding 10, surcharge -0.01",
        track_visibility='onchange')
    price_min_margin = fields.Float(
        'Min. Price Margin', digits='Product Price',
        help='Specify the minimum amount of margin over the base price.',
        track_visibility='onchange')
    price_max_margin = fields.Float(
        'Max. Price Margin', digits='Product Price',
        help='Specify the maximum amount of margin over the base price.',
        track_visibility='onchange')
    product_id = fields.Many2one(
        'product.product', 'Product', ondelete='cascade',
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.",
        track_visibility='onchange')
    categ_id = fields.Many2one(
        'product.category', 'Product Category', ondelete='cascade',
        help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.",
        track_visibility='onchange')
    price_surcharge = fields.Float(
        'Price Surcharge', digits='Product Price',
        help='Specify the fixed amount to add or substract(if negative) to the amount calculated with the discount.')
    price_discount = fields.Float('Price Discount', default=0, digits=(16, 2))
    percent_price = fields.Float('Percentage Price')
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        readonly=True, related='partner_id.currency_id', store=True)

    fixed_price = fields.Float('Fixed Price', digits='Product Price', track_visibility='onchange')

    product_gross_weight = fields.Float(string='Brutto', name='Net weight greater than',
                                        help="If product weight is greater or equal to this value then rules will be applied.",
                                        track_visibility='onchange')
    min_uvp = fields.Float(name='Min. UVP', copy=True, default=0.00, track_visibility='onchange')

    is_advance_domain = fields.Boolean(string="Advance Filter ?", copy=True, help="With this option you can set your custom filter for the pricelist selection.")

    advance_domain = fields.Char(string='Domain', default=[])

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        if self.applied_on != '0_product_variant':
            self.product_id = False
        if self.applied_on != '2_product_category':
            self.categ_id = False

    @api.model
    def create(self, vals):
        last_rec = self.search([('partner_id', '=', vals.get("partner_id",0))], order='sequence desc', limit=1)
        last_rec = last_rec.sequence + 1 if last_rec else 0
        vals.update(sequence=last_rec)
        res = super(PartnerPricelistItem, self).create(vals)

        return res

class PartnerSalePricelistItem(models.Model):
    _name = 'partner.sale.pricelist.item'
    _description = 'Vendor Sale price list'
    _inherit = ['partner.pricelist.item']
    _order = 'sequence, partner_id'

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        if self.applied_on != '0_product_variant':
            self.product_id = False
        if self.applied_on != '2_product_category':
            self.categ_id = False

    @api.model
    def create(self, vals):
        last_rec = self.search([('partner_id', '=', vals.get("partner_id", 0))], order='sequence desc', limit=1)
        last_rec = last_rec.sequence + 1 if last_rec else 0
        vals.update(sequence=last_rec)
        res = super(PartnerPricelistItem, self).create(vals)

        return res

