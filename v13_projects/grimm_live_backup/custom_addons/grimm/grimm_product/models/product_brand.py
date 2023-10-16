# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductBrand(models.Model):
    _inherit = 'grimm.product.brand'

    @api.model
    def _get_default_instructions(self):
        """ Get selected lines to add to exchange """
        instruction_ids = self.env['return.instruction'] \
            .search([('is_default', '=', True)], limit=1)
        return instruction_ids

    warranty_type = fields.Many2one('product.warranty.type', string='Warranty Type', copy=True)
    warranty_duration = fields.Float('Warranty Duration', copy=True,
                                     help="Warranty in month for this product/supplier relation. Only "
                                          "for company/supplier relation (purchase order) ; the  "
                                          "customer/company relation (sale order) always use the "
                                          "product main warranty field")
    return_instructions = fields.Many2one('return.instruction', 'Instructions', default=_get_default_instructions,
                                          help="Instructions for product return", copy=True)

    accessory_warranty_type = fields.Many2one('product.warranty.type', string='Warranty Type for Accessory', copy=True)
    accessory_warranty_duration = fields.Float('Warranty Duration for Accessory', copy=True)
    sparepart_warranty_type = fields.Many2one('product.warranty.type', string='Warranty Type for Sparepart', copy=True)
    sparepart_warranty_duration = fields.Float('Warranty Duration for Sparepart', copy=True)
