# -*- coding: utf-8 -*-

import copy

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_magento.components.mapper import  normalize_datetime
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
import requests
import json
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class ProductTemplateExportMapper(Component):
    _name = 'shopware6.product.template.export.mapper'
    _inherit = 'shopware6.product.template.export.mapper'
    _apply_on = ['shopware6.product.template']

    @changed_by('template_shopware6_category_ids','shopware6_category_ids')
    @mapping
    def assign_categories(self, record):
        return_dict = {}
        categ_list = []
        product_adapter = self.component(usage='backend.adapter', model_name='shopware6.product.product')

        categories = record.template_shopware6_category_ids if record.product_variant_count > 1 else record.shopware6_category_ids

        for categ in categories:
            for categ_binding in categ.shopware6_bind_ids:
                if categ_binding.shopware6_id:
                    categ_list.append({"id": categ_binding.shopware6_id})
        if categ_list:
            return_dict["categories"] = categ_list
        if record.shopware6_id:
            shopware_categ_data = product_adapter.get_assign_categories(record.shopware6_id)
            for categ in shopware_categ_data:
                if categ.get("id") not in [list(data.values())[0] for data in categ_list]:
                    product_adapter.del_assign_categories(record.shopware6_id, categ.get("id"))
        return return_dict

    @changed_by('product_brand_id')
    @mapping
    def map_manufacturer_id(self, record):
        return_dict = {}

        if record.product_brand_id:
            for bind in record.product_brand_id.shopware6_brand_ids:
                return_dict["manufacturerId"] = bind.shopware6_id
        if record.manufacture_code:
            return_dict["manufacturerNumber"] = record.manufacture_code
        return return_dict

    @changed_by('width', 'height', 'length', 'weight')
    @mapping
    def map_dimension_fields(self, record):
        return_dict = {}
        return_dict["width"] = str(record.width) if record.width else "0"
        return_dict["height"] = str(record.height) if record.height else "0"
        #return_dict["length"] = str(record.length) if record.length else "0"
        return_dict["length"] = str(record.depth) if record.depth else "0" # As suggestion from christian map depth with shopware length field.        return_dict["weight"] = str(record.weight) if record.weight else "0"
        return return_dict

    @changed_by('shopware6_sale_unit', 'shopware6_sale_unit_measure', 'packaging_unit', 'packaging_unit_plural', 'shopware6_base_unit')
    @mapping
    def map_unit_data(self, record):
        return_dict = {}
        return_dict["purchaseUnit"] = record.shopware6_sale_unit if record.shopware6_sale_unit else 0
        return_dict["referenceUnit"] = record.shopware6_base_unit if record.shopware6_base_unit else 0
        return_dict["packUnit"] = record.packaging_unit if record.packaging_unit else ""
        return_dict["packUnitPlural"] = record.packaging_unit_plural if record.packaging_unit_plural else ""
        if record.shopware6_sale_unit_measure:
            return_dict["unitId"] = record.shopware6_sale_unit_measure.shopware6_id
        return return_dict

    @changed_by('is_package', 'package_id')
    @mapping
    def assign_package_qty(self, record):
        return_dict = {}
        if record.is_package and record.package_id:
            return_dict["packUnit"] = "0"
            return_dict["packUnitPlural"] = "0"
            return_dict["minPurchase"] = int(record.package_id.qty_no or 0)
            return_dict["purchaseSteps"] = int(record.package_id.qty_no or 0)
        return return_dict

    @changed_by('default_code')
    @mapping
    def assign_miscellaneous_field(self, record):
        return_dict = super(ProductTemplateExportMapper, self).assign_miscellaneous_field(record)
        return_dict["productNumber"] = str(record.base_default_code) or str(record.openerp_id.id)
        return return_dict

    @changed_by('shopware6_delivery_time_id')
    @mapping
    def map_delivery_time_id(self, record):
        return_dict = {}
        if record.shopware6_delivery_time_id and record.shopware6_delivery_time_id.shopware6_id:
                return_dict["deliveryTimeId"] = record.shopware6_delivery_time_id.shopware6_id
        return return_dict

    @mapping
    def assign_price(self, record):
        super(ProductTemplateExportMapper, self).assign_price(record)
        #Here override assign price.

        currency_id = record.backend_id.shopware6_currency_id
        tax_id = False
        net_price = record.calculated_magento_price
        original_magento_price = net_price
        original_magento_price_with_tax = net_price
        # list_price = record.special_price #calculated_standard_price

        from_date = to_date = ""
        is_special_price = False

        current_time = datetime.now() + timedelta(hours=2)
        if record.special_price and (record.special_price_from or record.special_price_to):
            if record.special_price_from and not record.special_price_to:
                from_date = record.special_price_from + timedelta(hours=2)
                to_date = current_time + timedelta(days=1)
            elif record.special_price_to and not record.special_price_from:
                from_date = current_time - timedelta(days=1)
                to_date = record.special_price_to + timedelta(hours=2)
            else:
                from_date = record.special_price_from + timedelta(hours=2)
                to_date = record.special_price_to + timedelta(hours=2)
            if from_date <= current_time <= to_date:
                net_price = record.special_price
                is_special_price = True

        gross_price = net_price
        rrp_price_with_tax = record.rrp_price
        tax_rate = False
        for tax in record.taxes_id:
            tax_id = tax
            break
        if tax_id:
            for mapping in record.backend_id.tax_mapping_ids:
                if mapping.odoo_tax_id == tax_id:
                    tax_rate = mapping.tax_rate
                    break
            if tax_rate:
                gross_price = net_price + ((tax_rate/100) * net_price)
                rrp_price_with_tax = rrp_price_with_tax + ((tax_rate / 100) * rrp_price_with_tax)
                original_magento_price_with_tax = original_magento_price_with_tax + ((tax_rate / 100) * original_magento_price_with_tax)

        return {} if record.price_on_request else {"price": [
            {
                "currencyId": currency_id,
                "net": net_price,
                "gross": gross_price,
                "linked": True,
                "listPrice": {} if record.price_on_request else {
                    "currencyId": currency_id,
                    "net": original_magento_price if is_special_price else 0,
                    "gross": original_magento_price_with_tax if is_special_price else 0,
                    "linked": True,
                    "listPrice": ''
                },
                "extensions": []
            }
        ]}

    @changed_by('ean_number', 'manufacture_code')
    @mapping
    def assign_ean_manufacturer_code(self, record):
        return_dict = {}
        return_dict["ean"] = record.ean_number or ""
        return return_dict

    #@changed_by('shopware_active')
    @mapping
    def map_shopware_active(self, record):
        return_dict = {}
        if record.active:
            return_dict["active"] = record.shopware_active
        else:
            return_dict["active"] = False
        return return_dict

    @mapping
    def set_main_variant(self, record):
        return_dict = {}
        return_dict["mainVariantId"] = None
        if record.shopware6_product_listing == 'single':
            product_id = record.main_variant_id
            for binding in product_id.shopware6_bind_ids:
                binder = self.binder_for('shopware6.product.product')
                shopware6_id = binder.to_external(binding)
                if shopware6_id:
                    return_dict["mainVariantId"] = shopware6_id
        return return_dict

    @changed_by('parent_product_listing',
                'dont_show_variant',
                'show_property',
                'show_value_number',
                'show_in_cross_selling',
                'shopware6_shopping_prio_id',
                'price_on_request', 'short_description', 'template_short_description', 'is_spare_part', 'rrp_price', 'used_in_manufacturer_listing', 'warranty_type', 'warranty', 'shopware6_delivery_time_id')
    @mapping
    def assign_custom_fields(self, record):
        return_dict = {}
        if record.warranty_type:
            warranty = record.warranty_type
            for line in warranty.magento_value_map_ids.filtered(lambda rec: rec.months_no == record.warranty and rec.magento_attr_value_id ):
                return_dict['grimm_customFields_guarantee'] = str(line.magento_attr_value_id.name).replace("_", " ")

        if record.product_variant_count > 1:
            return_dict["short_description"] = record.template_short_description or ""
            return_dict["grimm_customFields_short_desc"] = record.template_short_description or ""
        else:
            return_dict["short_description"] = record.short_description or ""
            return_dict["grimm_customFields_short_desc"] = record.short_description or ""
        return_dict["custom_clerk_shipping_time"] = record.shopware6_delivery_time_id.name if record.shopware6_delivery_time_id else ""
        return_dict["custom_clerk_net_price"] = record.calculated_magento_price
        for tax in record.taxes_id:
            return_dict["custom_clerk_vat"] = tax.amount
            break

        return_dict["grimm_customFields_replacement"] = record.is_spare_part
        return_dict["grimm_customfields_feed_custom_label_0"] = record.shopware6_shopping_prio_id.name if record.shopware6_shopping_prio_id else ''
        if record.used_in_manufacturer_listing:
            return_dict["grimm_customfields_show_on_manufactuer_page"] = record.used_in_manufacturer_listing
        return_dict["grimm_customFields_uvp"] = str(record.rrp_price)
        return_dict["grimm_customfields_productRequest_only"] = record.price_on_request

        return_dict["mkx_better_variants_use_parent_data"] = record.parent_product_listing
        return_dict["mkx_better_variants_hide_variants"] = record.dont_show_variant
        return_dict["mkx_better_variants_show_groups"] = record.show_property
        return_dict["mkx_better_variants_show_group_numbers"] = record.show_value_number
        return_dict["mkx_better_variants_show_in_cross_selling"] = record.show_in_cross_selling

        if return_dict:
            return {"customFields":return_dict}
        return return_dict

    @changed_by('meta_description', 'meta_title' 'rrp_price')
    @mapping
    def assign_meta_information(self, record):
        return_dict = {}
        # if record.meta_description:
        #     return_dict["metaDescription"] = record.meta_title
        # if record.meta_title:
        #     return_dict["metaTitle"] = record.meta_title
        # As per suggestion from Tobias not sending these value (OD-1216)

        return return_dict

    @changed_by('search_words')
    @mapping
    def assign_search_keywords(self, record):
        words = []
        for word in record.search_words:
            words.append(word.name)
        return {"customSearchKeywords": words}

    @changed_by('grimm_product_custom_product_template_id')
    @mapping
    def assign_custom_product_id(self, record):
        return_dict = {}
        return_dict["description"] = "" if record.description == '<p><br></p>' or record.description == '' or not record.description else record.description
        return_dict["swagCustomizedProductsTemplateId"] = None
        if record.grimm_product_custom_product_template_id:
            for binding in record.grimm_product_custom_product_template_id.shopware6_bind_ids:
                if binding.shopware6_id:
                    return_dict["swagCustomizedProductsTemplateId"] = binding.shopware6_id
                    break

        return return_dict

    @changed_by('technical_specifications')
    @mapping
    def property_assignment(self, record):
        return_dict = []
        for attribute in record.technical_specifications:
            for binding in attribute.value_ids.shopware6_bind_ids:
                if binding.shopware6_id:
                    return_dict.append({"id":binding.shopware6_id})
        return {"properties":return_dict}

class ProductProductExportMapperShopware6(Component):
    _name = 'shopware6.product.product.export.mapper'
    _inherit = 'shopware6.product.product.export.mapper'
    _apply_on = ['shopware6.product.product']

    @changed_by('product_brand_id')
    @mapping
    def map_manufacturer_id(self, record):
        return_dict = {}
        if record.product_brand_id:
            for bind in record.product_brand_id.shopware6_brand_ids:
                return_dict["manufacturerId"] = bind.shopware6_id
        if record.manufacture_code:
            return_dict["manufacturerNumber"] = record.manufacture_code
        return return_dict

    @changed_by('width', 'height', 'length', 'weight')
    @mapping
    def map_dimension_fields(self, record):
        return_dict = {}
        return_dict["width"] = str(record.width) if record.width else "0"
        return_dict["height"] = str(record.height) if record.height else "0"
        # return_dict["length"] = str(record.length) if record.length else "0"
        return_dict["length"] = str(record.depth) if record.depth else "0"  # As suggestion from christian map depth with shopware length field.
        return_dict["weight"] = str(record.weight) if record.weight else "0"
        return return_dict

    @changed_by('shopware6_sale_unit', 'shopware6_sale_unit_measure', 'packaging_unit', 'packaging_unit_plural',
                'shopware6_base_unit')
    @mapping
    def map_unit_data(self, record):
        return_dict = {}
        return_dict["purchaseUnit"] = record.shopware6_sale_unit if record.shopware6_sale_unit else 0
        return_dict["referenceUnit"] = record.shopware6_base_unit if record.shopware6_base_unit else 0
        return_dict["packUnit"] = record.packaging_unit if record.packaging_unit else ""
        return_dict["packUnitPlural"] = record.packaging_unit_plural if record.packaging_unit_plural else ""
        if record.shopware6_sale_unit_measure:
            return_dict["unitId"] = record.shopware6_sale_unit_measure.shopware6_id
        return return_dict

    @changed_by('is_package', 'package_id')
    @mapping
    def assign_package_qty(self, record):
        return_dict = {}
        if record.is_package and record.package_id:
            return_dict["packUnit"] = "0"
            return_dict["packUnitPlural"] = "0"
            return_dict["minPurchase"] = int(record.package_id.qty_no or 0)
            return_dict["purchaseSteps"] = int(record.package_id.qty_no or 0)
        return return_dict

    @changed_by('search_words')
    @mapping
    def assign_search_keywords(self, record):
        words = []
        for word in record.search_words:
            words.append(word.name)
        return {"customSearchKeywords": words}

    @changed_by('shopware6_delivery_time_id')
    @mapping
    def map_delivery_time_id(self, record):
        return_dict = {}
        if record.shopware6_delivery_time_id and record.shopware6_delivery_time_id.shopware6_id:
            return_dict["deliveryTimeId"] = record.shopware6_delivery_time_id.shopware6_id
        return return_dict

    #@changed_by('shopware_active')
    @mapping
    def map_shopware_active(self, record):
        return_dict = {}
        if record.active:
            return_dict["active"] = record.shopware_active
        else:
            return_dict["active"] = False
        return return_dict

    @changed_by('ean_number', 'manufacture_code')
    @mapping
    def assign_ean_manufacturer_code(self, record):
        return_dict = {}
        return_dict["ean"] = record.ean_number or ""
        return return_dict

    @changed_by('meta_description', 'meta_title')
    @mapping
    def assign_meta_information(self, record):
        return_dict = {}
        # if record.meta_description:
        #     return_dict["metaDescription"] = record.meta_title
        # if record.meta_title:
        #     return_dict["metaTitle"] = record.meta_title
        # As per suggestion from Tobias not sending these value (OD-1216)

        return return_dict

    @changed_by('price_on_request','short_description', 'is_spare_part', 'rrp_price', 'used_in_manufacturer_listing', 'warranty_type', 'warranty', 'shopware6_delivery_time_id', 'shopware6_shopping_prio_id')
    @mapping
    def assign_custom_fields(self, record):
        return_dict = {}
        if record.warranty_type:
            warranty = record.warranty_type
            for line in warranty.magento_value_map_ids.filtered(lambda rec: rec.months_no == record.warranty and rec.magento_attr_value_id ):
                return_dict['grimm_customFields_guarantee'] = str(line.magento_attr_value_id.name).replace("_", " ")
        if record.short_description:
            return_dict["short_description"] = record.short_description
            return_dict["grimm_customFields_short_desc"] = record.short_description

        if record.shopware6_delivery_time_id:
            return_dict["custom_clerk_shipping_time"] = record.shopware6_delivery_time_id.name
        return_dict["custom_clerk_net_price"] = record.calculated_magento_price
        for tax in record.taxes_id:
            return_dict["custom_clerk_vat"] = tax.amount
            break

        return_dict["grimm_customFields_replacement"] = record.is_spare_part
        return_dict["grimm_customFields_uvp"] = str(record.rrp_price)
        if record.used_in_manufacturer_listing:
            return_dict["grimm_customfields_show_on_manufactuer_page"] = record.used_in_manufacturer_listing
        return_dict["grimm_customfields_productRequest_only"] = record.price_on_request
        return_dict["grimm_customfields_feed_custom_label_0"] = record.shopware6_shopping_prio_id.name if record.shopware6_shopping_prio_id else ''
        if return_dict:
            return {"customFields":return_dict}
        return return_dict

    @changed_by('technical_specifications')
    @mapping
    def property_assignment(self, record):
        return_dict = []
        for attribute in record.technical_specifications:
            for binding in attribute.value_ids.shopware6_bind_ids:
                if binding.shopware6_id:
                    return_dict.append({"id":binding.shopware6_id})
        return {"properties":return_dict}

    @changed_by('shopware6_price_trigger')
    @mapping
    def send_price_shopware6(self, record):
        '''
        This mapping method only created for price trigger.
        :param record:
        :return:
        '''
        res = self.assign_price(record)
        return res

    @mapping
    def assign_price(self, record):
        super(ProductProductExportMapperShopware6, self).assign_price(record)
        currency_id = record.backend_id.shopware6_currency_id
        tax_id = False

        net_price = record.calculated_magento_price
        original_magento_price = net_price
        original_magento_price_with_tax = net_price

        from_date = to_date = ""
        is_special_price = False

        current_time = datetime.now() + timedelta(hours=2)
        if record.special_price and (record.special_price_from or record.special_price_from):
            if record.special_price_from and not record.special_price_to:
                from_date = record.special_price_from + timedelta(hours=2)
                to_date = current_time + timedelta(days=1)
            elif record.special_price_to and not record.special_price_from:
                from_date = current_time - timedelta(days=1)
                to_date = record.special_price_to + timedelta(hours=2)
            else:
                from_date = record.special_price_from + timedelta(hours=2)
                to_date = record.special_price_to + timedelta(hours=2)
            if from_date <= current_time <= to_date:
                net_price = record.special_price
                is_special_price = True

        gross_price = net_price
        rrp_price_with_tax = record.rrp_price
        tax_rate = False
        for tax in record.taxes_id:
            tax_id = tax
            break
        if tax_id:
            for mapping in record.backend_id.tax_mapping_ids:
                if mapping.odoo_tax_id == tax_id:
                    tax_rate = mapping.tax_rate
                    break
            if tax_rate:
                gross_price = net_price + ((tax_rate / 100) * net_price)
                rrp_price_with_tax = rrp_price_with_tax + ((tax_rate / 100) * rrp_price_with_tax)
                original_magento_price_with_tax = original_magento_price_with_tax + ((tax_rate / 100) * original_magento_price_with_tax)

        return {} if record.price_on_request else {"price": [
            {
                "currencyId": currency_id,
                "net": net_price,
                "gross": gross_price,
                "linked": True,
                "listPrice":  {
                    "currencyId": currency_id,
                    "net": original_magento_price if is_special_price else 0,
                    "gross": original_magento_price_with_tax if is_special_price else 0,
                    "linked": True,
                    "listPrice": ''
                },
                "extensions": []
            }
        ]}

    @changed_by('grimm_product_custom_product_template_id','description')
    @mapping
    def assign_custom_product_id(self, record):
        return_dict = {}
        return_dict["description"] = "" if record.description == '<p><br></p>' or record.description == '' or not record.description else record.description
        custom_product_template = record.grimm_product_custom_product_template_id
        if record.grimm_custom_product_use_parent_template:
            custom_product_template = record.product_tmpl_id.grimm_product_custom_product_template_id
        return_dict["swagCustomizedProductsTemplateId"] = None
        if custom_product_template:
            for binding in custom_product_template.shopware6_bind_ids:
                if binding.shopware6_id:
                    return_dict["swagCustomizedProductsTemplateId"] = binding.shopware6_id
                    break
        return return_dict


class Shopware6ProductTemplateExporter(Component):
    _name = 'shopware6.product.template.exporter'
    _inherit = 'shopware6.product.template.exporter'
    _apply_on = ['shopware6.product.template']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        res = super(Shopware6ProductTemplateExporter, self)._export_dependency(binding)
        if binding.openerp_id.product_brand_id:
            brand_bind = binding.backend_id.create_bindings_for_model(binding.openerp_id.product_brand_id, 'shopware6_brand_ids')

        # for attribute in binding.openerp_id.attribute_data_ids:
        #     new_attribute_binding = binding.backend_id.create_bindings_for_model(attribute.attr_id, 'shopware6_bind_ids')
        for attribute in binding.openerp_id.technical_specifications:
            new_attribute_binding = binding.backend_id.create_bindings_for_model(attribute.attr_id, 'shopware6_bind_ids')
        # for attribute in binding.openerp_id.textual_attribute_data_ids:
        #     new_attribute_binding = binding.backend_id.create_bindings_for_model(attribute.attr_id, 'shopware6_bind_ids')

        #Export custom product template
        if binding.openerp_id.grimm_product_custom_product_template_id:
            binding.openerp_id.grimm_product_custom_product_template_id.export_to_shopware6()

        for accessory in binding.openerp_id.accessory_part_ids:
            if accessory.accessory_part_id.active:
                accessory.accessory_part_id.with_context(export_now=True).export_to_shopware6()

        return res

    def _after_export(self):
        res = super(Shopware6ProductTemplateExporter, self)._after_export()
        # Assign Sale Channel START
        product_template = self.binding.openerp_id
        updated_fields = self.fields
        if updated_fields is not None and ('ignore_after_export' in updated_fields or 'shopware6_price_trigger' in updated_fields):
            return res
        sales_channel_fields = ['channel_ids','main_categ_id']
        if updated_fields is None or any(item in updated_fields for item in sales_channel_fields):
            odoo_channels = []
            odoo_channel_visiblity = {}
            for channel in self.binding.channel_ids:
                if channel.channel_id and channel.channel_id.shopware6_id:
                    odoo_channels.append(channel.channel_id.shopware6_id)
                    odoo_channel_visiblity[channel.channel_id.shopware6_id] = channel.visiblity
            shopware_channels = self.backend_adapter.get_assign_channels(self.binding.shopware6_id)
            for channel in shopware_channels:
                try:
                    self.backend_adapter.del_assign_channels(channel.get("id"))
                except:
                    pass

            shopware_main_category = self.backend_adapter.get_assigned_main_category(self.binding.shopware6_id)
            for main in shopware_main_category:
                self.backend_adapter.del_assign_main_category(main.get("id"))

            for channel in list(set(odoo_channels)):
                try:
                    self.backend_adapter.assign_channels(self.binding.shopware6_id, {"salesChannelId": channel,"visibility": int(odoo_channel_visiblity.get(channel, "30"))})
                except:
                    pass
                if product_template.main_categ_id:
                    main_categ_vals = {"salesChannelId": channel, "productId": self.binding.shopware6_id, "categoryId": False}
                    for categ_bind in product_template.main_categ_id.shopware6_bind_ids:
                        main_categ_vals["categoryId"] = categ_bind.shopware6_id
                    if main_categ_vals.get("categoryId", False):
                        return_id = self.backend_adapter.create_update_main_category(main_categ_vals)


        image_fields = ['image_ids', 'product_media_ids']
        if updated_fields is None or any(item in updated_fields for item in image_fields):
            for image in product_template.image_ids:
                export_property = self.binding.backend_id.create_bindings_for_model(image, 'shopware6_bind_ids')

        odoo_properties_fields = ['technical_specifications']
        if updated_fields is None or any(item in updated_fields for item in odoo_properties_fields):
            odoo_properties = []
            for attribute in product_template.technical_specifications:
                for value in attribute.value_ids:
                    for binding in value.shopware6_bind_ids:
                        if binding.shopware6_id:
                            odoo_properties.append(binding.shopware6_id)

            product_data = self.backend_adapter.read_proprties(self.binding.shopware6_id)
            shopware_properties = []
            for data in product_data:
                shopware_properties.append(data.get("id"))
            for shopware_property_id in shopware_properties:
                if shopware_property_id not in odoo_properties:
                    delete_property = self.backend_adapter.delete_proprties(self.binding.shopware6_id,shopware_property_id)

        create_update_vals = {
            "name": "Zubehör",
            "sortBy": "name",
            "sortDirection": "ASC",
            "type": "productList",
            "active": True,
            "limit": 2444,
            "productId": self.binding.shopware6_id,
        }

        if self.binding.openerp_id.is_accessorypart_cross and self.binding.openerp_id.accessory_part_ids:
            if self.binding.openerp_id.cross_selling_id:
                update_cross_selling = self.backend_adapter.create_update_cross_selling(create_update_vals, self.binding.openerp_id.cross_selling_id)
            else:
                cross_selling_id = self.backend_adapter.create_update_cross_selling(create_update_vals)
                self.binding.openerp_id.with_context(connector_no_export=True).write({'cross_selling_id': cross_selling_id})

        if self.binding.openerp_id.cross_selling_id:
            for accessory in self.binding.openerp_id.accessory_part_ids:
                if accessory.accessory_part_id.active:
                    self.binding.backend_id.create_bindings_for_model(accessory, 'shopware6_bind_ids')

        return res

class Shopware6ProductProductExporter(Component):
    _name = 'shopware6.product.product.exporter'
    _inherit = 'shopware6.product.product.exporter'
    _apply_on = ['shopware6.product.product']
    _usage = 'record.exporter'

    def get_shopware6_id(self,product_id):
        for bind in product_id.shopware6_bind_ids:
            return bind.shopware6_id if bind.shopware6_id else False
        for bind in product_id.shopware6_pt_bind_ids:
            return bind.shopware6_id if bind.shopware6_id else False
    def _export_dependency(self,binding):
        res = super(Shopware6ProductProductExporter, self)._export_dependency(binding)
        if binding.openerp_id.product_brand_id:
            brand_bind = binding.backend_id.create_bindings_for_model(binding.openerp_id.product_brand_id, 'shopware6_brand_ids')

        #Export custom product template
        if binding.openerp_id.grimm_product_custom_product_template_id:
            binding.openerp_id.grimm_product_custom_product_template_id.export_to_shopware6()

        #Export technical specification
        for attribute in binding.openerp_id.technical_specifications:
            new_attribute_binding = binding.backend_id.create_bindings_for_model(attribute.attr_id, 'shopware6_bind_ids')

        #Export accessory part as a dependancy.
        for accessory in binding.openerp_id.accessory_part_ids:
            if accessory.accessory_part_id.active:
                accessory.accessory_part_id.with_context(export_now=True).export_to_shopware6()

        return res

    def _after_export(self):
        res = super(Shopware6ProductProductExporter, self)._after_export()
        product_product = self.binding.openerp_id
        updated_fields = self.fields
        if updated_fields is not None and ('ignore_after_export' in updated_fields or 'shopware6_price_trigger' in updated_fields):
            return res

        # Assign Sale Channel START
        updated_fields = self.fields
        sales_channel_fields = ['channel_ids','main_categ_id']
        if updated_fields is None or any(item in updated_fields for item in sales_channel_fields):
            odoo_channels = []
            odoo_channel_visiblity = {}
            for channel in self.binding.channel_ids:
                if channel.channel_id and channel.channel_id.shopware6_id:
                    odoo_channels.append(channel.channel_id.shopware6_id)
                    odoo_channel_visiblity[channel.channel_id.shopware6_id] = channel.visiblity
            shopware_channels = self.backend_adapter.get_assign_channels(self.binding.shopware6_id)
            for channel in shopware_channels:
                try:
                    self.backend_adapter.del_assign_channels(channel.get("id"))
                except:
                    pass

            shopware_main_category = self.backend_adapter.get_assigned_main_category(self.binding.shopware6_id)
            for main in shopware_main_category:
                self.backend_adapter.del_assign_main_category(main.get("id"))

            for channel in list(set(odoo_channels)):
                try:
                    self.backend_adapter.assign_channels(self.binding.shopware6_id,{"salesChannelId": channel, "visibility": int(odoo_channel_visiblity.get(channel,"30"))})
                except:
                    pass
                if product_product.main_categ_id:
                    main_categ_vals = {"salesChannelId": channel, "productId": self.binding.shopware6_id, "categoryId": False}
                    for categ_bind in product_product.main_categ_id.shopware6_bind_ids:
                        main_categ_vals["categoryId"] = categ_bind.shopware6_id
                    if main_categ_vals.get("categoryId", False):
                        return_id = self.backend_adapter.create_update_main_category(main_categ_vals)


        image_fields = ['image_ids', 'product_media_ids', 'variant_image_ids']
        if updated_fields is None or any(item in updated_fields for item in image_fields):
            if product_product.product_tmpl_id.product_variant_count == 1:
                for image in product_product.product_tmpl_id.image_ids:
                    export_property = self.binding.backend_id.create_bindings_for_model(image, 'shopware6_bind_ids')
            for image in product_product.variant_image_ids:
                export_property = self.binding.backend_id.create_bindings_for_model(image, 'shopware6_bind_ids')

        #if product_product.product_tmpl_id.product_variant_count == 1:
        if product_product.accessory_part_ids:
            create_update_vals = {
                "name": "Zubehör",
                "sortBy": "name",
                "sortDirection": "ASC",
                "type": "productList",
                "active": True,
                "limit": 2444,
                "productId": self.binding.shopware6_id,
            }

            if product_product.is_accessorypart_cross and product_product.accessory_part_ids:
                if product_product.cross_selling_id:
                    update_cross_selling = self.backend_adapter.create_update_cross_selling(create_update_vals, product_product.cross_selling_id)
                else:
                    cross_selling_id = self.backend_adapter.create_update_cross_selling(create_update_vals)
                    product_product.with_context(connector_no_export=True).write({'cross_selling_id': cross_selling_id})

            if product_product.cross_selling_id:
                for accessory in product_product.accessory_part_ids:
                    if accessory.accessory_part_id.active:
                        self.binding.backend_id.create_bindings_for_model(accessory, 'shopware6_bind_ids')

        odoo_properties_fields = ['technical_specifications']
        if updated_fields is None or any(item in updated_fields for item in odoo_properties_fields):
            odoo_properties = []
            for attribute in product_product.technical_specifications:
                for binding in attribute.value_ids.shopware6_bind_ids:
                    if binding.shopware6_id:
                        odoo_properties.append(binding.shopware6_id)

            product_data = self.backend_adapter.read_proprties(self.binding.shopware6_id)
            shopware_properties = []
            for data in product_data:
                shopware_properties.append(data.get("id"))

            for shopware_property_id in shopware_properties:
                if shopware_property_id not in odoo_properties:
                    delete_property = self.backend_adapter.delete_proprties(self.binding.shopware6_id,shopware_property_id)

        try:
            # We have Implemeneted to send latest custom product template. OD-1344 (Custom Product Price)
            custom_product_template_option_value = self.env['grimm_custom_product.option_value'].sudo().search([('use_product_price', '=', True),('product_id', '=', product_product.product_tmpl_id.id)])
            for cptv in custom_product_template_option_value:
                if cptv.option_id and cptv.option_id.template_id:
                    for custom_binding in cptv.shopware6_bind_ids:
                        custom_binding.export_record(fields=[])
        except:
            pass
        return res
