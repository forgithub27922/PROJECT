# -*- coding: utf-8 -*-


from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends('seller_ids')
    def _get_supplier_article_numbers(self):
        for product in self:
            article_numbers = []
            for seller in product.seller_ids:
                if seller.product_code:
                    article_numbers.append(seller.product_code)
            product.supplier_article_numbers = ", ".join(article_numbers)

    seller_ids = fields.One2many(copy=True)
    supplier_article_numbers = fields.Char(
        string="Supplier Article Number", compute='_get_supplier_article_numbers')
    # default_code = fields.Char(string="Internal Reference",
    #                           related="product_variant_ids.default_code", store=False)
    supplier_name = fields.Char(
        string="Supplier", related="seller_ids.name.display_name", store=False)
    net_weight = fields.Float(string='Net Weight')
    default_code = fields.Char(string='Internal Reference', track_visibility='onchange')
    description = fields.Text(
        'Description', translate=True,
        help="A precise description of the Product, used only for internal information purposes.",
        track_visibility='onchange')


class ProductBrand(models.Model):
    _inherit = 'grimm.product.brand'
    warranty_type = fields.Many2one('product.warranty.type', string='Warranty Type')
