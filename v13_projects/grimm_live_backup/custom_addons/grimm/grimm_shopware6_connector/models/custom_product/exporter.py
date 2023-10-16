# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class CustomProductTemplateMapperShopware6(Component):
    _name = 'shopware6.grimm_custom_product.template.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.grimm_custom_product.template']

    direct = [
        ('name', 'displayName'),
        ('technical_name', 'internalName'),
        ('active', 'active'),
        ('step_by_step_mode', 'stepByStep'),
        ('options_auto_collapse', 'optionsAutoCollapse'),
        ('need_confirmation', 'confirmInput'),
        ('description', 'description'),
    ]

    # @mapping
    # def set_image_record(self, record):
    #     return_res = {}
    #     return_res['mediaId'] = "19f58417f06847b798dac7ca761165a6"
    #     # if record.shopware6_media_id:
    #     #     return_res['templateId'] = record.template_id.shopware6_bind_ids[0].shopware6_id
    #     return return_res

class CustomProductOptionMapperShopware6(Component):
    _name = 'shopware6.grimm_custom_product.option.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.grimm_custom_product.option']

    direct = [
        ('name', 'displayName'),
        ('type', 'type'),
        ('description', 'description'),
    ]

    @mapping
    def set_multiselect(self, record):
        res = {}
        res["position"] = record.sequence
        res["typeProperties"] = {}
        if record.type == "select":
            res["typeProperties"] = {
                    "isMultiSelect": True if record.multiselect else False
                }
        return res

    @mapping
    def set_metainformation(self, record):
        return_res = {}
        if record.type == "checkbox":
            if record.value.sku:
                return_res["itemNumber"] = record.value.sku
            elif record.value.product_id:
                return_res["itemNumber"] = record.value.product_id.default_code

        if record.type == "select":
            return_res["required"] = record.required
        return return_res

    @mapping
    def set_tax_id(self, record):
        return_dict = {}
        if record.type == "checkbox":
            for tax in record.value.product_id.taxes_id:
                tax_mapping = record.backend_id.tax_mapping_ids.filtered(lambda r: r.odoo_tax_id.id == tax.id)
                tax_mapping = tax_mapping[0] if tax_mapping else False
                if tax_mapping:
                    return_dict["taxId"] = tax_mapping.shopware6_id
                    break
        return return_dict

    @mapping
    def set_price(self, record):
        return_res = {
            "price": [
                {
                    "net": 0,
                    "gross": 0,
                    "currencyId": record.backend_id.shopware6_currency_id,
                    "linked": True,
                }
            ],
        }
        if record.type == "checkbox":
            return_res = {
                "price": [
                    {
                        "net": record.value.price,
                        "gross": record.value.price,
                        "currencyId": record.backend_id.shopware6_currency_id,
                        "linked": True,
                    }
                ],
            }
            if record.value.use_product_price:
                tax_id = False
                net_price = record.value.product_id.calculated_magento_price
                gross_price = net_price
                for tax in record.value.product_id.taxes_id:
                    tax_id = tax
                    break
                if tax_id:
                    for mapping in record.backend_id.tax_mapping_ids:
                        if mapping.odoo_tax_id == tax_id:
                            tax_rate = mapping.tax_rate
                            break
                    if tax_rate:
                        gross_price = net_price + ((tax_rate / 100) * net_price)

                return_res["price"][0]["net"] = net_price
                return_res["price"][0]["gross"] =gross_price
        return return_res

    @mapping
    def set_custom_template_id(self, record):
        return_res = {}
        if record.template_id.shopware6_bind_ids:
            if record.template_id.shopware6_bind_ids[0].shopware6_id:
                return_res['templateId'] = record.template_id.shopware6_bind_ids[0].shopware6_id
        return return_res

class CustomProductOptionValueMapperShopware6(Component):
    _name = 'shopware6.grimm_custom_product.option.value.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.grimm_custom_product.option_value']

    direct = [
        ('name', 'displayName')
    ]

    @mapping
    def set_templateOptionId(self, record):
        return_res = {}
        if record.option_id.shopware6_bind_ids:
            if record.option_id.shopware6_bind_ids and record.option_id.shopware6_bind_ids[0].shopware6_id:
                return_res['templateOptionId'] = record.option_id.shopware6_bind_ids[0].shopware6_id
        return_res["position"] = record.position if record.position else 1
        return return_res

    @mapping
    def set_sku(self, record):
        return_res = {}
        if record.sku:
            return_res["itemNumber"] = record.sku
        elif record.product_id:
            return_res["itemNumber"] = record.product_id.default_code
        return return_res

    @mapping
    def set_tax_id(self, record):
        return_dict = {}
        for tax in record.product_id.taxes_id:
            tax_mapping = record.backend_id.tax_mapping_ids.filtered(lambda r: r.odoo_tax_id.id == tax.id)
            tax_mapping = tax_mapping[0] if tax_mapping else False
            if tax_mapping:
                return_dict["taxId"] = tax_mapping.shopware6_id
                break
        return return_dict

    @mapping
    def set_price(self, record):
        return_res = {
            "price": [
                {
                    "net": record.price,
                    "gross": record.price,
                    "currencyId": record.backend_id.shopware6_currency_id,
                    "linked": True,
                }
            ],
        }
        if record.use_product_price:
            tax_id = False
            net_price = record.product_id.calculated_magento_price
            gross_price = net_price
            for tax in record.product_id.taxes_id:
                tax_id = tax
                break
            if tax_id:
                for mapping in record.backend_id.tax_mapping_ids:
                    if mapping.odoo_tax_id == tax_id:
                        tax_rate = mapping.tax_rate
                        break
                if tax_rate:
                    gross_price = net_price + ((tax_rate / 100) * net_price)

            return_res["price"][0]["net"] = net_price
            return_res["price"][0]["gross"] = gross_price
        return return_res



class Shopware6CustomProductTemplateExporter(Component):
    _name = 'shopware6.grimm_custom_product.template.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.grimm_custom_product.template']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        # if binding.openerp_id.parent_id:
        #     export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.parent_id, 'shopware6_bind_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6CustomProductTemplateExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        if self.binding.openerp_id.image:
            config_setting = self.backend_adapter.create_assign_media(self.binding)
        for option in self.binding.openerp_id.option_ids:
            bind_value = self.binding.backend_id.create_bindings_for_model(option, 'shopware6_bind_ids')
        pass

class Shopware6CustomProductOptionExporter(Component):
    _name = 'shopware6.grimm_custom_product.option.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.grimm_custom_product.option']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        # if binding.openerp_id.parent_id:
        #     export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.parent_id, 'shopware6_bind_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6CustomProductOptionExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        if self.binding.openerp_id.type == "select":
            for val in self.binding.openerp_id.values:
                bind_value = self.binding.backend_id.create_bindings_for_model(val, 'shopware6_bind_ids')
        pass

class Shopware6CustomProductOptionValueExporter(Component):
    _name = 'shopware6.grimm_custom_product.option.value.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.grimm_custom_product.option_value']
    _usage = 'record.exporter'

class CustomProductTemplateDeleterShopware6(Component):
    _name = 'shopware6.grimm_custom_product.template.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.grimm_custom_product.template','shopware6.grimm_custom_product.option', 'shopware6.grimm_custom_product.option_value']
    _usage = 'record.exporter.deleter'
