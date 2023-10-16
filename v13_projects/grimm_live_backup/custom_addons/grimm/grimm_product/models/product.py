# -*- coding: utf-8 -*-


from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends('seller_ids', 'seller_ids.product_code')
    def _get_supplier_article_numbers(self):
        """ build a list of supplier article numbers """
        #self.ensure_one()
        for product in self:
            article_numbers = [seller.product_code for seller in product.seller_ids if seller.product_code]
            product.supplier_article_numbers = ", ".join(article_numbers)

    seller_ids = fields.One2many(copy=True)
    supplier_article_numbers = fields.Char(string="Supplier Article Number", compute='_get_supplier_article_numbers')
    warranty_type = fields.Many2one('product.warranty.type', string='Warranty Type', copy=True)
    warranty = fields.Float(
        'Warranty Duration',
        help="Warranty in month for this product/supplier relation. Only "
             "for company/supplier relation (purchase order) ; the  "
             "customer/company relation (sale order) always use the "
             "product main warranty field", copy=True)
    has_variants = fields.Boolean('Has variants?', default=False)
    attribute_set_id = fields.Many2one('product.attribute.set', string='Attribute set', copy=True)
    attribute_data_ids = fields.One2many(comodel_name='product.attributes.data', inverse_name='product_tmpl_id',
                                         string='Attributes data', copy=True)



    @api.onchange('product_brand_id')
    def _onchange_product_brand(self):
        """ get warranty_type and warranty_duration automatic from product brand """
        for product in self:
            if not product.product_brand_id:
                continue
            #if product.is_spare_part:
            #    product.warranty_type = product.product_brand_id.sparepart_warranty_type
            #    product.warranty = product.product_brand_id.sparepart_warranty_duration
            #elif product.is_accessory_part:
            #    product.warranty_type = product.product_brand_id.accessory_warranty_type
            #    product.warranty = product.product_brand_id.accessory_warranty_duration
            #else:
            product.warranty_type = product.product_brand_id.warranty_type
            product.warranty = product.product_brand_id.warranty_duration


class ProductProduct(models.Model):
    _inherit = 'product.product'

    attribute_set_id = fields.Many2one('product.attribute.set', related='product_tmpl_id.attribute_set_id', store=True,
                                       string='Attribute set')


class ProductAttributesData(models.Model):
    _name = 'product.attributes.data'
    _description = 'Product attribute data'

    product_tmpl_id = fields.Many2one('product.template', 'Product Template', required=True, ondelete='cascade')
    attr_id = fields.Many2one('product.attribute', 'Attribute', required=True, ondelete='restrict')
    value_id = fields.Many2one('product.attribute.value', string='Attribute value')

    # _sql_constraints = [ #odoo13change
    #     ('attribute_product_tmpl_uniq', 'UNIQUE(attr_id, product_tmpl_id)',
    #         'Multiple attribute values!')
    # ]
