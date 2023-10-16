# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from odoo import models, fields, api

from .product_attribute import PRODUCT_ATTRIBUTE_TYPES
from ..constants import (
    ATTRS_ODOO_MASTER, ATTRS_MAGENTO_MASTER, PRODUCTS_MAGENTO_MASTER, PRODUCTS_ODOO_MASTER,
    NO_IMAGES_SYNC, BASIC_IMAGES_SYNC, FULL_IMAGES_SYNC_BASE, FULL_IMAGES_SYNC_ALL
)


# from odoo.addons.magentoerpconnect.unit.import_synchronizer import import_batch
# from odoo.addons.magentoerpconnect.unit.import_synchronizer import import_record


class MagentoBackend(models.Model):
    _inherit = 'magento.backend'

    team_webhook_url = fields.Char('Team Webhook URL', help="Here you can enter webhook url so odoo will call after product creation.")

    fiscal_mapping_ids = fields.One2many(
        comodel_name='country.fiscal.position.map',
        inverse_name='backend_id', string='Fiscal position mappings'
    )

    tax_mapping_ids = fields.One2many('magento.tax.mapping', 'backend_id', string='Magento tax mappings')

    product_system_val_ids = fields.One2many('default.product.system.vals', 'backend_id',
                                             string='Default product system values')

    product_attributes_sync_type = fields.Selection(
        selection=[
            (ATTRS_ODOO_MASTER, 'Export from Odoo to Magento'),
            (ATTRS_MAGENTO_MASTER, 'Import from Magento to Odoo')
        ], string='Synchronization type', required=True, default=ATTRS_MAGENTO_MASTER
    )

    products_sync_type = fields.Selection(
        selection=[
            (PRODUCTS_ODOO_MASTER, 'Export from Odoo to Magento'),
            (PRODUCTS_MAGENTO_MASTER, 'Import from Magento to Odoo'),
        ], string='Products synchronization', required=True, default=PRODUCTS_ODOO_MASTER
    )

    product_images_import_type = fields.Selection(
        selection=[
            (NO_IMAGES_SYNC, 'No images synchronization'),
            (BASIC_IMAGES_SYNC, 'Basic images synchronization'),
            (FULL_IMAGES_SYNC_BASE, 'Full images synchronization (base image only)'),
            (FULL_IMAGES_SYNC_ALL, 'Full images synchronization (all images)'),
        ], string='Catalog images import type', required=True, default=BASIC_IMAGES_SYNC
    )

    product_images_export_type = fields.Selection(
        selection=[
            (NO_IMAGES_SYNC, 'No images synchronization'),
            (FULL_IMAGES_SYNC_ALL, 'Full images synchronization (all images)'),
        ], string='Catalog images export type', required=True, default=FULL_IMAGES_SYNC_ALL
    )

    import_categories = fields.Boolean(
        string='Import product categories?',
        default=False,
        help="Should product categories be imported during import of products"
    )

    import_configurable_products_from_date = fields.Datetime(string='Import products from date')
    force_import_of_variants = fields.Boolean('Force import of all variants after configurable product import?',
                                              default=False)
    synch_product_translations = fields.Boolean("Synchronize product translations?", default=False)

    import_attributes_of_type = fields.Selection(selection=PRODUCT_ATTRIBUTE_TYPES, string='Import attributes of type')
    import_attributes_from_set = fields.Many2one(comodel_name='product.attribute.set', string='Attribute set')
    admin_storeview_id = fields.Many2one('magento.storeview', string='Admin Storeview')

    single_record_magento_id = fields.Char('Record Id on Magento')
    single_model_to_import = fields.Selection(
        selection=[
            ('magento.sale.order', 'Sale order'),
            ('product.product', 'Product'),
        ], string='Model to import', default='magento.sale.order'
    )

    is_product_variant = fields.Boolean(
        'Is variant product?',
        help="""Make sure that you select this option only if product belongs to configurable product on Magento side.
                If you select it for standalone simple product it won't be imported as standalone product in Odoo!!!""")

    single_variant_parent_id = fields.Many2one('product.template', string='Variant parent',
                                               domain=[('magento_type', '=', 'configurable')])

    default_product_ctg_id = fields.Integer(string='Default category magento ID')
    disable_checkpoints = fields.Boolean('Disable checkpoints?')

    def write(self, vals):
        if not self._context.get('skip_config_date_update', False) and 'import_products_from_date' in vals:
            vals['import_configurable_products_from_date'] = vals['import_products_from_date']

        res = super(MagentoBackend, self).write(vals)
        return res

    @api.model
    def select_versions(self):
        res = super(MagentoBackend, self).select_versions()
        res.append(('1.7.1', 'Openfellas Magento Extensions (1.7+)'))
        return res

    def _prepare_default_binding_vals(self, record):
        self.ensure_one()
        return {
            'backend_id': self.id,
            'openerp_id': record.id
        }

    def create_bindings_for_model(self, record, bindings_field_name):
        self.ensure_one()

        existing_binds = record[bindings_field_name].filtered(lambda rec: rec.backend_id.id == self.id)

        if not existing_binds:
            binding_vals = self._prepare_default_binding_vals(record)
            if hasattr(record, '_prepare_specific_binding_vals'):
                binding_vals.update(record._prepare_specific_binding_vals(self))
            res = self.env[record[bindings_field_name]._name].create(binding_vals)
        else:
            res = existing_binds

        return res

    def import_attribute_sets(self):
        for backend in self:
            backend.check_magento_structure()
            self.env['magento.product.attribute.set'].with_delay().import_batch(
                backend,
            )
        return True

    def import_attributes(self):
        for backend in self:
            if backend.product_attributes_sync_type != ATTRS_MAGENTO_MASTER:
                continue
            backend.check_magento_structure()

            attribute_set = None
            if backend.import_attributes_from_set:
                attribute_set = backend.import_attributes_from_set.magento_binding_ids.filtered(
                    lambda binding: binding.backend_id.id == backend.id
                )

            self.env['magento.product.attribute'].with_delay().import_batch(backend, attribute_set)
        return True

    def import_product_images(self):
        for backend in self:
            if backend.product_images_import_type == NO_IMAGES_SYNC:
                continue
            backend.check_magento_structure()
            self.env['magento.product.image'].with_delay().import_batch(backend)
        return True

    def import_product_product(self):
        for backend in self:
            if backend.products_sync_type == PRODUCTS_MAGENTO_MASTER:
                history = self.env['products.import.history'].create({'backend_id': backend.id})
                backend.with_context(import_history_id=history.id)._import_from_date(
                    'magento.product.template', 'import_configurable_products_from_date'
                )

                backend.with_context(import_history_id=history.id, skip_config_date_update=True)._import_from_date(
                    'magento.product.product', 'import_products_from_date'
                )

    # @api.multi
    # def _import_specific_product(self, magento_sku):
    #     self.ensure_one()
    #
    #     assert self.single_model_to_import in ('product.product',)
    #     from ..units.product_import import import_configurable_product, import_product, initial_import_variant_product
    #     from ..units.product_adapter import OpenfellasProductAdapter
    #     from ..connector_env import get_environment
    #
    #     if not magento_sku:
    #         return
    #
    #     jobs = self.env['queue.job'].search([
    #         ('model_name', 'in', ('magento.product.template', 'magento.product.product')),
    #         ('state', 'not in', ('failed', 'done'))
    #     ])
    #
    #     if jobs:
    #         raise Warning(_(
    #             'It is not recommended that you import products manually while there are executing queue jobs related to products.'))
    #
    #     # session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
    #     # env = get_environment(session, 'magento.product.product', self.id)
    #     env = self.work_on('magento.product.product')
    #     # product_adapter = env.component(usage='')
    #     product_adapter = env.get_connector_unit(OpenfellasProductAdapter)
    #
    #     try:
    #         product_magento_data = product_adapter._call('ol_catalog_product.info', [magento_sku, None, None, 'sku'])
    #     except Exception as ex:
    #         product_magento_data = {}
    #
    #     magento_id = product_magento_data.get('product_id', None)
    #     product_type = product_magento_data.get('type_id', None)
    #
    #     if not (product_type or magento_id):
    #         raise Warning(_('Could not extract product data!'))
    #
    #     if product_type == 'configurable':
    #         product_model = 'magento.product.template'
    #     else:
    #         product_model = 'magento.product.product'
    #
    #     history = self.env['products.import.history'].create({'backend_id': self.id})
    #
    #     if product_model == 'magento.product.template':
    #         if self.is_product_variant:
    #             raise Warning(_('This product can not be variant!'))
    #
    #         import_configurable_product.delay(session, 'magento.product.template', self.id, magento_id, history.id,
    #                                           True)
    #
    #     if product_model == 'magento.product.product':
    #         existing = self.env['magento.product.product'].with_context(active_test=False).search(
    #             [('magento_id', '=', magento_id)])
    #
    #         if existing or not self.is_product_variant:
    #             import_product.delay(session, 'magento.product.product', self.id, magento_id, history.id, force=True)
    #
    #         elif self.is_product_variant:
    #             ptmpl_binding = self.single_variant_parent_id.magento_ptmpl_bind_ids.filtered(
    #                 lambda rec: rec.backend_id.id == self.id and rec.magento_id
    #             )
    #
    #             if not ptmpl_binding:
    #                 raise Warning(_('This variant does not exists in Odoo. You must select parent product.'))
    #
    #             parent_magento_id = int(ptmpl_binding.magento_id)
    #
    #             initial_import_variant_product.delay(session, 'magento.product.product', self.id, magento_id,
    #                                                  parent_magento_id, history.id, force=True)
    #
    #     return True

    def import_single_record(self):
        for backend in self:
            backend.check_magento_structure()

            if self.single_model_to_import in ('magento.sale.order',):
                self.env['magento.res.partner.category'].with_delay().import_batch(backend.id,
                                                                                   backend.single_record_magento_id)
            # we don't import product from magento anymore
            # if self.single_model_to_import in ('product.product',):
            #     self._import_specific_product(self.single_record_magento_id)

        return True

    @api.onchange('is_product_variant')
    def onchange_is_product_variant(self):
        if not self.is_product_variant:
            self.single_variant_parent_id = False


class MagentoTaxMapping(models.Model):
    _name = 'magento.tax.mapping'
    _description = 'Magento tax mapping'

    tax_id = fields.Many2one('account.tax', string='Tax', required=True)
    magento_tax_percent = fields.Float(string='Magento tax percent', required=True)
    backend_id = fields.Many2one('magento.backend', string='Magento backend')

    _sql_constraints = [('tax_amount_backend_unique', 'unique (tax_id,magento_tax_percent,backend_id)',
                         'Tax mapping must be unique per backend!')]


class CountryFiscalPositionMap(models.Model):
    _name = 'country.fiscal.position.map'
    _description = 'Country fiscal position map'

    backend_id = fields.Many2one('magento.backend', string='Magento backend')
    country_id = fields.Many2one('res.country', string='Country', required=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal position', required=True)

    _sql_constraints = [
        ('country_uniq', 'unique (country_id, backend_id)',
         'There can be only one fiscal position for country per backend!')
    ]


class DefaultProductSystemVals(models.Model):
    _name = 'default.product.system.vals'
    _description = 'Default product system vals'

    backend_id = fields.Many2one('magento.backend', string='Magento backend')
    magento_attribute_id = fields.Many2one('magento.product.attribute', string='Product attribute', required=True)
    magento_attr_value_id = fields.Many2one('magento.product.attribute.value', string='Value', required=True)
