# -*- coding: utf-8 -*-


from odoo import models, fields, api

import odoo.addons.decimal_precision as dp


class ProductConnectionMedium(models.Model):
    _name = "product.connection.medium"
    _description = "Connection Medium"
    _description = 'Product connection medium'

    name = fields.Char("Medium", required=True)


class ProductConnectionUnit(models.Model):
    _name = "product.connection.unit"
    _description = "Connection Unit"
    _description = 'Product connection unit'

    name = fields.Char("Unit Name", required=True)


class ProductConnection(models.Model):
    _name = 'product.connection'
    _description = 'Product connection'

    connection_medium = fields.Many2one('product.connection.medium', string='Connection Medium')
    connection_spec = fields.Char(string='Connection Spec')
    connection_value = fields.Float(string='Connetion Value')
    connection_unit = fields.Many2one('product.connection.unit', string='Connection Unit')
    product_id = fields.Many2one('product.template', string='Connection Type')
    asset_id = fields.Many2one('grimm.asset.asset', string='Asset')

class ProductDocumentType(models.Model):
    _name = 'product.document.type'
    _description = 'Product documents Types'

    name = fields.Char(string='Name', required=True)

class ProductDocument(models.Model):
    _name = 'product.document'
    _description = 'Product documents'

    product_tmpl_id = fields.Many2one('product.template', string='Artikelstamm', ondelete='cascade')
    name = fields.Char(string='Name')
    filename = fields.Char(string='Datei Name')
    attachment = fields.Binary('Datei', attachment=True)
    is_public = fields.Boolean('Is Public?', default=False)
    document_type = fields.Many2one('product.document.type', string='Document Type')

    @api.onchange('filename')
    def onchange_filename(self):
        self.name = self.filename


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _calculate_lump_sums(self):
        for record in self:
            amount = 0
            for service_part in record.service_part_ids:
                amount += service_part.lump_sum
            record.service_part_lump_sums = amount

    is_spare_part = fields.Boolean('Spare Part', default=False)
    is_tool = fields.Boolean('Tool', default=False)
    is_accessory_part = fields.Boolean('Accessory Part', default=False)
    is_service_part = fields.Boolean('Service Part', default=False)

    is_forwarding_good = fields.Boolean('Speditionsgut', default=False)
    is_express_shipping = fields.Boolean('Express-Shipping', default=False)

    product_brand_id = fields.Many2one('grimm.product.brand', string='Brand')

    service_part_ids = fields.One2many(
        'service.part.product', 'product_id', string='Service Parts')
    accessory_part_ids = fields.One2many(
        'accessory.part.product', 'product_id', string='Accessory Parts', copy=True)
    spare_part_ids = fields.Many2many(
        'product.template', 'product_spare_rel', 'src_id', 'dest_id', string='Spare Parts')
    tool_ids = fields.Many2many(
        'product.template', 'product_tool_rel', 'src_id', 'dest_id', string='Tools')
    service_part_lump_sums = fields.Float(
        compute=_calculate_lump_sums, string='Total lump sum', digits='Product Price')
    product_attachment_ids = fields.One2many(
        'product.document', 'product_tmpl_id', string='Dokumente', copy=True)
    connection_ids = fields.One2many(
        'product.connection', 'product_id', string='Connections')


class ServicePartProduct(models.Model):
    _name = 'service.part.product'
    _description = 'Service Part and Quantity'

    service_part_id = fields.Many2one('product.template', string='Service Product')
    # product_id = fields.Many2one('product.template', string='Related Product', domain=[
    #                             ('is_service_part', '=', True)])
    product_id = fields.Many2one('product.template', string='Related Product')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure',
                            required=True, default=1)
    lump_sum = fields.Float(string='Lump sum', digits='Product Price')

    _sql_constraints = [('service_part_unique', 'unique (service_part_id,product_id)',
                         'You can not assign same service part twice.!')]


class AccessoryPartProduct(models.Model):
    _name = 'accessory.part.product'
    _description = 'Accessory Part and Quantity'

    accessory_part_id = fields.Many2one('product.template', string='Accessory Product')
    # product_id = fields.Many2one('product.template', string='Related Product', domain=[
    #                             ('is_accessory_part', '=', True)])
    product_id = fields.Many2one('product.template', string='Related Product')
    product_sale_price = fields.Float(related='product_id.list_price', readonly=True)
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure',
                            required=True, default=1)

    _sql_constraints = [('accessory_part_unique', 'unique (accessory_part_id,product_id)',
                         'You can not assign same accessory part twice.!')]
