# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.of_base_magento_extensions_v9.constants import DEFAULT_TAX_CLASS_ID
from odoo.addons.of_base_magento_extensions_v9.units.product.exporter import (ProductExportMapper,
                                                                              ConfigurableProductExportMapper)
from odoo.tools.translate import _
import logging
from slugify import slugify

_logger = logging.getLogger(__name__)

class ProductExporter(Component):
    _name = 'magento.product.product.exporter'
    _inherit = 'magento.product.product.exporter'
    _apply_on = ['magento.product.product']
    _usage = 'record.exporter'

    def _after_export(self):
        super(ProductExporter, self)._after_export()
        binding = self.binding
        existed_link = self.backend_adapter.search_product_link('related', binding.magento_id)
        new_link = []
        position_dict = {}
        for accessory in binding.openerp_id.accessory_part_ids:
            for m_ids in accessory.accessory_part_id.magento_pp_bind_ids:
                new_link.append(int(m_ids.magento_id))
                position_dict[m_ids.magento_id] = accessory.position if accessory.position else 0

        for spare_part in binding.openerp_id.spare_part_prod_ids:
            for m_ids in spare_part.spare_part_id.magento_pp_bind_ids:
                new_link.append(int(m_ids.magento_id))
                position_dict[m_ids.magento_id] = spare_part.position if spare_part.position else 0

        remove_link = list(set(list(set(existed_link) - set(new_link))))
        remove_link = list(set(remove_link))
        new_link = list(set(new_link))
        for link in remove_link:
            try:
                is_removed = self.backend_adapter.remove_product_link('related', binding.magento_id, link)
            except:
                continue #in some cases product has been deleted from magento but still we have reference in odoo. So when odoo call received error from magento.
        for link in new_link:
            try:
                is_added = self.backend_adapter.assign_product_link('related', binding.magento_id, link, {'position': position_dict.get(str(link), 0)})
            except:
                continue #in some cases product has been deleted from magento but still we have reference in odoo. So when odoo call received error from magento.

class CommonProductExportMappings(Component):
    _name = 'magento.product.common.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = [
        'magento.product.template',
        'magento.product.product',
        #'magento.template.product'
    ]
    _usage = 'magento.product.common.export.mapper'

    def descriptions(self, record):
        return {
            'description': record.description,
            'short_description': record.short_description
        }

    def categories(self, record):
        category_ids = {}

        for categ in record.categ_ids:
            magento_bind_ids = categ.magento_bind_ids.filtered(lambda rec: rec.backend_id == record.backend_id)
            if magento_bind_ids:
                category_ids[int(magento_bind_ids[0].magento_id)] = True
        if record.categ_id:
            magento_bind_ids = record.categ_id.magento_bind_ids.filtered(lambda rec: rec.backend_id == record.backend_id)
            if magento_bind_ids:
                category_ids[int(magento_bind_ids[0].magento_id)] = True
        if record.magento_category_id and record.magento_category_id.magento_id: # Commented code to transfer extra category only to magento OD-812
           category_ids[int(record.magento_category_id.magento_id)] = True

        if not category_ids and self.backend_record.default_product_ctg_id:
            category_ids[int(self.backend_record.default_product_ctg_id)] = True

        if len(category_ids) == 0:
            raise Warning(_('Product category is not properly set!'))

        return {'categories': list(category_ids.keys())}

    def warranty_data(self, record):
        res = {
            'grimm_warranty_time': False
        }

        if record.warranty_type:
            warranty = record.warranty_type
            attr_value_binding = warranty.get_magento_warranty_value(record.warranty, self.backend_record.id)

            if attr_value_binding and attr_value_binding.magento_id:
                res['grimm_warranty_time'] = attr_value_binding.magento_id

        return res

    def brand(self, record):
        res = {
        }

        if record.product_brand_id:
            attr_val_bind = record.product_brand_id.get_magento_brand_value(self.backend_record.id)

            if attr_val_bind:
                res['grimm_manufacturer'] = attr_val_bind.magento_id

        return res

    def magento_status(self, record, field_name):
        res = {}

        if record[field_name]:
            status = record[field_name].get_magento_status_value(self.backend_record.id)

            if status and status.magento_id:
                res['status'] = status.magento_id

        return res

    def price(self, record):
        product = record.with_context(
            quantity=1,
            pricelist=self.backend_record.pricelist_id.id,
            currency_id=self.backend_record.pricelist_id.currency_id.id
        )
        sale_price = product.calculated_magento_price
        if not sale_price:
            return {}
        try:
            res = {'price': sale_price, 'price_lp': product.rrp_price, 'cost': product.standard_price, 'no_price_calc': '0'}
        except:
            res = {'price': sale_price, 'price_lp': product.rrp_price, 'cost': product.standard_price, 'no_price_calc': '0'}
        return res

    def tax_class(self, record):
        taxes = record.taxes_id.filtered(
            lambda rec: rec.magento_tax_class_id and rec.magento_tax_class_id.magento_binding_ids)
        magento_tax_class_id = None
        try:
            magento_tax_class_id = taxes and taxes[0].magento_binding_ids[0].magento_id
        except:
            pass
        if not magento_tax_class_id:
            magento_tax_class_id = DEFAULT_TAX_CLASS_ID
        return {'tax_class_id': magento_tax_class_id}

    def delivery_time(self, record):
        try:
            return {'grimm_delivery_time': record.magento_delivery_time.magento_binding_ids[0].magento_id}
        except:
            return {'grimm_delivery_time': None}

    def used_in_manufacturer_listing(self, record):
        try:
            return {
                'used_in_manufacturer_listing': record.used_in_manufacturer_listing}
        except:
            return {'used_in_manufacturer_listing': None}

    def magento_visibility(self, record):
        try:
            return {
                'visibility': record.magento_visibility.magento_binding_ids[0].magento_id}
        except:
            return {'visibility': None}


class GrimmProductExportMapper(ProductExportMapper):
    _name = 'magento.product.product.export.mapper'
    _inherit = 'magento.product.product.export.mapper'
    _apply_on = ['magento.product.product']

    grimm_direct = [
        ('height', 'height'),
        ('width', 'width'),
        ('depth', 'depth'),
        ('connection', 'anschluss'),
        ('net_weight', 'weight'),
        #('special_price', 'special_price'),
        #('special_price_from', 'special_from_date'),
        #('special_price_to', 'special_to_date'),
        ('ean_number', 'ean'), ('meta_autogenerate', 'meta_autogenerate'), ('meta_title', 'meta_title'),
        ('meta_keyword', 'meta_keyword'),
        ('meta_description', 'meta_description')
    ]

    grimm_remove_mappings = [
        ('description_sale', 'description'),
        ('description', 'short_description')
    ]

    direct = list(set(ProductExportMapper.direct).union(set(grimm_direct)) - set(grimm_remove_mappings))

    def __init__(self, connector_env):
        super(GrimmProductExportMapper, self).__init__(connector_env)
        self.common_mapper = self.component(usage='magento.product.common.export.mapper')

    @changed_by('description', 'short_description')
    @mapping
    def descriptions(self, record):
        res = self.common_mapper.descriptions(record)
        return res

    @mapping
    def set_special_price(self, record):
        res = {
            'special_from_date': record.special_price_from,
            'special_to_date': record.special_price_to,
        }
        if record.special_price <= 0:
            res["special_price"] = False
        else:
            res["special_price"] = record.special_price
        return res

    # @mapping
    # @changed_by('product_link_related_ids')
    # def product_link(self, record):
    #     export_product_link.delay(
    #         self.session, 'magento.product.link', self.backend_record.id, record.magento_id, record.id
    #     )

    def _change_umlauts(self, prod_name):
        prod_name = prod_name.replace('ü', 'ue')
        prod_name = prod_name.replace('Ü', 'Ue')
        prod_name = prod_name.replace('ä', 'ae')
        prod_name = prod_name.replace('Ä', 'Ae')
        prod_name = prod_name.replace('ö', 'oe')
        prod_name = prod_name.replace('Ö', 'Oe')
        prod_name = prod_name.replace('ß', 'ss')
        return prod_name

    @changed_by('name')
    @mapping
    def map_url_key(self, record):
        prod_name = self._change_umlauts(record.name)
        return {
            'url_key': slugify(prod_name)
        }

    @changed_by('categ_id', 'categ_ids')
    @mapping
    def categories(self, record):
        res = self.common_mapper.categories(record)
        return res

    @mapping
    def assign_ersatzteil(self, record):
        return {'ersatzteil': True if record.is_spare_part else False, 'ean':record.ean_number}

    @changed_by('taxes_id')
    @mapping
    def tax_class(self, record):
        res = self.common_mapper.tax_class(record)
        return res

    @changed_by('warranty', 'warranty_type')
    @mapping
    def warranty_data(self, record):
        res = self.common_mapper.warranty_data(record)
        return res

    @changed_by('product_brand_id')
    @mapping
    def brand(self, record):
        res = self.common_mapper.brand(record)
        return res

    @mapping
    @changed_by('variant_product_status_id')
    def magento_variant_status(self, record):
        res = self.common_mapper.magento_status(record, 'variant_product_status_id')
        return res

    @mapping
    @changed_by('magento_product_status_id')
    def magento_status(self, record):
        res = self.common_mapper.magento_status(record, 'magento_product_status_id')
        return res

    @mapping
    @changed_by('list_price', 'lst_price', 'seller_ids', 'update_prices_trigger', 'rrp_price',
                'price_calculation_group')
    def price(self, record):
        res = self.common_mapper.price(record)
        return res

    @mapping
    @changed_by('magento_delivery_time')
    def delivery_time(self, record):
        res = self.common_mapper.delivery_time(record)
        return res

    @mapping
    @changed_by('used_in_manufacturer_listing')
    def used_in_manufacturer_listing(self, record):
        res = self.common_mapper.used_in_manufacturer_listing(record)
        return res

    @mapping
    @changed_by('magento_visibility')
    def magento_visibility(self, record):
        res = self.common_mapper.magento_visibility(record)
        return res


class GrimmConfigurableProductExportMapper(ConfigurableProductExportMapper):
    _name = 'magento.product.configurable.export.mapper'
    _inherit = 'magento.product.configurable.export.mapper'
    #_apply_on = ['magento.template.product']
    _apply_on = ['magento.product.template']

    grimm_direct = [
        ('connection', 'anschluss'),
        ('ean_number', 'ean')
    ]

    grimm_remove_mappings = [
        ('description_sale', 'description'),
        ('description', 'short_description'),
        ('list_price', 'price'),
        #('special_price', 'special_price'),
        ('special_price_from', 'special_from_date'),
        ('special_price_to', 'special_to_date'),
        ('meta_autogenerate', 'meta_autogenerate'), ('meta_title', 'meta_title'), ('meta_keyword', 'meta_keyword'),
        ('meta_description', 'meta_description')
    ]

    direct = list(set(ConfigurableProductExportMapper.direct).union(set(grimm_direct)) - set(grimm_remove_mappings))

    def __init__(self, connector_env):
        super(GrimmConfigurableProductExportMapper, self).__init__(connector_env)
        self.common_mapper = self.component(usage='magento.product.common.export.mapper')

    @changed_by('description', 'short_description')
    @mapping
    def descriptions(self, record):
        res = self.common_mapper.descriptions(record)
        return res

    @only_create
    @mapping
    @changed_by('categ_id', 'categ_ids')
    def categories(self, record):
        res = self.common_mapper.categories(record)
        return res

    @changed_by('taxes_id')
    @mapping
    def tax_class(self, record):
        res = self.common_mapper.tax_class(record)
        return res

    @changed_by('warranty', 'warranty_type')
    @mapping
    def warranty_data(self, record):
        res = self.common_mapper.warranty_data(record)
        return res

    @changed_by('product_brand_id')
    @mapping
    def brand(self, record):
        res = self.common_mapper.brand(record)
        return res

    @mapping
    @changed_by('magento_product_status_id')
    def magento_status(self, record):
        res = self.common_mapper.magento_status(record, 'magento_product_status_id')
        return res

    @mapping
    @changed_by('magento_delivery_time')
    def delivery_time(self, record):
        res = self.common_mapper.delivery_time(record)
        return res

    @mapping
    @changed_by('used_in_manufacturer_listing')
    def used_in_manufacturer_listing(self, record):
        res = self.common_mapper.used_in_manufacturer_listing(record)
        return res

    @mapping
    @changed_by('magento_visibility')
    def magento_visibility(self, record):
        res = self.common_mapper.magento_visibility(record)
        return res

    @mapping
    @changed_by('list_price', 'lst_price', 'seller_ids', 'update_prices_trigger', 'rrp_price',
                'price_calculation_group')
    def price(self, record):
        res = self.common_mapper.price(record)
        return res
