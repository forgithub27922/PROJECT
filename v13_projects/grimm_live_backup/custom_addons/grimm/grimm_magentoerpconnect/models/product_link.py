# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductLink(models.Model):
    _name = 'product.link'
    _description = 'Magento Product Link for relation, up-selling, cross-selling'
    _order = 'sequence,position,name'

    type = fields.Selection(
        selection=[('related', 'Related'), ('cross_sell', 'Cross Selling'), ('up_sell', 'Up Selling'),
                   ('grouped', 'Grouped')], string="Type", copy=True)
    position = fields.Integer(string='Position')
    sequence = fields.Integer(string='Sequence')
    name = fields.Many2one(comodel_name='product.template', string='Product Template', copy=True, ondelete='cascade')
    linked_product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product Template',
                                             copy=True, ondelete='cascade')
    default_code = fields.Char(string='Article Number', related='name.default_code', readonly=True)

    magento_bind_ids = fields.One2many(
        comodel_name='magento.product.link',
        inverse_name='openerp_id',
        string="Magento Bindings",
    )


class MagentoSaleOrder(models.Model):
    _name = 'magento.product.link'
    _inherit = 'magento.binding'
    _description = 'Magento Product Link'
    _inherits = {'product.link': 'openerp_id'}

    openerp_id = fields.Many2one(comodel_name='product.link',
                                 string='Odoo Product Link',
                                 required=True,
                                 ondelete='cascade')

    magento_main_product_id = fields.Many2one(
        'magento.product.product',
        compute='_compute_products',
        ondelete='cascade',
        store=True,
        help='Main Magento Product'
    )
    magento_linked_product_id = fields.Many2one(
        'magento.product.product',
        compute='_compute_products',
        ondelete='cascade',
        store=True,
        help='Linked Magento Product'
    )
