# -*- coding: utf-8 -*-


from odoo import models, fields, api

from ..constants import PRODUCTS_ODOO_MASTER, FULL_IMAGES_SYNC_ALL, CONFIGURABLE_PRODUCT
from odoo.addons.component_event import skip_if
from slugify import slugify


class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Product image'
    _order = 'sequence'

    product_tmpl_id = fields.Many2one('product.template', string='Standalone product', ondelete='cascade')
    variant_product_id = fields.Many2one('product.product', string='Variant product', ondelete='cascade')
    is_automatic_image = fields.Boolean(string='Automatic image', compute='_is_automatic_img', store=False)

    name = fields.Char('Name', required=True)
    file_name = fields.Char('File Name')
    sequence = fields.Integer(string='Sort order')
    transfer_to_magento = fields.Boolean(string='Transfer to Magento', default=False)
    transfer_to_shopware = fields.Boolean(string='Transfer to Shopware', default=False)
    transfer_to_ebay = fields.Boolean(string='Transfer to eBay', default=False)
    is_base_image = fields.Boolean(string='Base image', default=False)
    is_small_image = fields.Boolean(string='Small image', default=False)
    is_thumbnail = fields.Boolean(string='Thumbnail', default=False)
    is_standard = fields.Boolean(string='Standard', default=False)
    sync_with_magento = fields.Boolean('Sync with Magento?', default=True)
    manual_image_data = fields.Binary(string='Image', attachment=True)
    automatic_image_data = fields.Binary(string='Image', compute='_get_automatic_image_data', store=False)
    binary_write_date = fields.Datetime(string='Image change date')
    magento_binding_ids = fields.One2many('magento.product.image', 'openerp_id', 'Magento bindings')
    should_export = fields.Boolean('Should export to Magento?', compute='_compute_should_export')
    #position = fields.Integer(string='Position', compute='_compute_position', store=True, readonly=True)
    position = fields.Integer(string='Position', store=True, readonly=True)
    license = fields.Selection([
        ('eigenes_werk', 'Eigenes Werk'),
        ('hersteller', 'Hersteller'),
        ('shutterstock', 'Shutterstock'),
        ('pixabay', 'Pixabay'),
        ('unsplash', 'Unsplash'),
        ('andere', 'Andere'),
    ], string='Lizenz', default='andere')
    original_link = fields.Char('Originallink')
    attribution = fields.Char('Namensnennung')

    @api.onchange('manual_image_data', 'position')
    def _compute_image_file_name(self):
        for record in self:
            if record.manual_image_data:
                filename = record.file_name if record.file_name else ""
                product_name = record.product_tmpl_id.name if record.product_tmpl_id.name else ""
                categ_name = record.product_tmpl_id.categ_id.name if record.product_tmpl_id.categ_id.name else ""
                full_name = slugify(product_name+"_"+categ_name+"_"+str(record.position))+"."+filename.split("." if "." in filename else "-")[-1]
                if slugify(product_name+"_"+categ_name+"_"+str(record.position)) != "0":
                    record.file_name = full_name

    @api.depends('sequence')
    def _compute_position(self):
        for product_tmpl in self.mapped('product_tmpl_id'):
            if not product_tmpl:
                continue
            line_num = 1
            # is_changed = False
            for image in product_tmpl.image_ids:
                image.position = line_num
                line_num += 1

    def _compute_should_export(self):
        backends = self.env['magento.backend'].search([
            ('products_sync_type', '=', PRODUCTS_ODOO_MASTER),
            ('product_images_export_type', '=', FULL_IMAGES_SYNC_ALL)
        ])

        for img in self:
            if not backends or not img.sync_with_magento:
                img.should_export = False
            else:
                for backend in backends:
                    product_is_exported = img._is_product_exported(backend)
                    img_has_bindings = len(
                        img.magento_binding_ids.filtered(lambda rec: rec.backend_id.id == backend.id)) > 0
                    img.should_export = product_is_exported and not img_has_bindings

    def _is_product_exported(self, backend):
        self.ensure_one()

        res = False
        product = self.product_tmpl_id or self.variant_product_id
        bindings_collection = None

        if product._name == 'product.template':
            if product.magento_type == CONFIGURABLE_PRODUCT:
                bindings_collection = product.magento_ptmpl_bind_ids
            else:
                bindings_collection = product.product_variant_ids and product.product_variant_ids[0].magento_bind_ids
        elif product._name == 'product.product':
            bindings_collection = product.magento_bind_ids

        if bindings_collection:
            binding = bindings_collection.filtered(lambda rec: rec.magento_id and rec.backend_id.id == backend.id)
            res = len(binding) > 0

        return res

    def _is_automatic_img(self):
        for img in self:
            img.is_automatic_image = img.is_standard

    def _get_automatic_image_data(self):
        for img in self:
            img_data = False

            if img.is_standard:
                if img.product_tmpl_id:
                    img_data = img.product_tmpl_id.image_1920
                elif img.variant_product_id:
                    img_data = img.variant_product_id.image_1920
                    #img_data = img.variant_product_id.image_variant

            img.automatic_image_data = img_data

    def export_to_magento(self):
        self.ensure_one()

        backends = self.env['magento.backend'].search([
            ('products_sync_type', '=', PRODUCTS_ODOO_MASTER),
            ('product_images_export_type', '=', FULL_IMAGES_SYNC_ALL)
        ])

        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'magento_binding_ids')

        return True


class MagentoProductImage(models.Model):
    _name = 'magento.product.image'
    _description = 'Magento Product Image'
    _inherit = 'magento.binding'
    _inherits = {
        'product.image': 'openerp_id'
    }

    openerp_id = fields.Many2one('product.image', required=True, ondelete='cascade')

    magento_ptmpl_id = fields.Many2one(
        'magento.product.template',
        compute='_compute_products',
        ondelete='cascade',
        store=True,
        help='If image belongs to configurable product'
    )

    magento_product_id = fields.Many2one(
        'magento.product.product',
        compute='_compute_products',
        required=False,
        store=True,
        ondelete='cascade',
        help='If image belongs to standalone or variant simple product'
    )

    @api.depends('openerp_id', 'openerp_id.product_tmpl_id', 'openerp_id.variant_product_id',
                 'openerp_id.product_tmpl_id.magento_ptmpl_bind_ids', 'openerp_id.variant_product_id.magento_bind_ids')
    def _compute_products(self):
        for record in self:
            mptmpl_res = False
            mpp_res = False

            ptmpl = record.openerp_id.product_tmpl_id
            prod = record.openerp_id.variant_product_id

            for ptmpl_binding in ptmpl.magento_ptmpl_bind_ids.filtered(
                    lambda rec: rec.backend_id.id == record.backend_id.id):
                mptmpl_res = ptmpl_binding.id
                break

            if not mptmpl_res:
                for pp in ptmpl.product_variant_ids:
                    for mpp in pp.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == record.backend_id.id):
                        mpp_res = mpp.id
                        break

                for mpp in prod.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == record.backend_id.id):
                    mpp_res = mpp.id
                    break

            record.magento_ptmpl_id = mptmpl_res
            record.magento_product_id = mpp_res

    _sql_constraints = [
        ('backend_oe_uniq', 'unique(backend_id, openerp_id)',
         'Odoo product image can be linked with only one product image per Magento backend!'),
    ]
