# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
import logging
_logger = logging.getLogger(__name__)

class ProductTemplateExportMapperShopware6(Component):
    _name = 'shopware6.product.template.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.product.template']

    direct = [
        ('name', 'name'),
        ('shopware_active', 'active')
    ]

    @changed_by('default_code', 'description')
    @mapping
    def assign_miscellaneous_field(self, record):
        return_dict = {}
        return_dict["productNumber"] = str(record.default_code) if record.default_code else str(record.openerp_id.id)
        return_dict["description"] = "" if record.description == '<p><br></p>' or record.description == '' else record.description
        #return_dict["swagCustomizedProductsTemplateId"] = "5793e2c3052b488994f1168dd41acd9f"
        return_dict["type"] = 'product'
        return return_dict

    @mapping
    def name_mapping(self, record):
        return_dict = {}
        return_dict["name"] = record.name
        return return_dict

    @changed_by('supplier_taxes_id', 'taxes_id')
    @mapping
    def assign_tax_id(self, record):
        return_dict = {}
        for tax in record.taxes_id:
            tax_mapping = record.backend_id.tax_mapping_ids.filtered(lambda r: r.odoo_tax_id.id == tax.id)
            tax_mapping = tax_mapping[0] if tax_mapping else False
            if tax_mapping:
                return_dict["taxId"] = tax_mapping.shopware6_id
                break
        return return_dict

    @changed_by('attribute_line_ids')
    @mapping
    def assign_configuratorSettings(self, record):
        return_dict = {}
        option_list = []
        total_option = record.config_setting.split("@") if record.config_setting else []
        for attribute in record.attribute_line_ids:
            for value in attribute.value_ids:
                for bind in value.shopware6_bind_ids:
                    if bind.shopware6_id not in total_option:
                        option_list.append({"optionId":bind.shopware6_id})
        if option_list:
            return_dict["configuratorSettings"] = option_list
        return return_dict

    @changed_by('shopware6_category_ids')
    @mapping
    def assign_categories(self, record):
        return_dict = {}
        categ_list = []
        product_adapter = self.component(usage='backend.adapter', model_name='shopware6.product.product')
        for categ in record.shopware6_category_ids:
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

    @mapping
    def assign_price(self, record):
        currency_id = record.backend_id.shopware6_currency_id
        return {"price": [
            {
                "currencyId": currency_id,
                "net": record.list_price,
                "gross": record.list_price,
                "linked": True,
                "listPrice": {
                    "currencyId": currency_id,
                    "net": record.standard_price,
                    "gross": record.standard_price,
                    "linked": True,
                    "listPrice": ''
                },
                "extensions": []
            }
        ]}

    @mapping
    def assign_stock(self, record):
        return_dict = {}
        return_dict["stock"] = int(getattr(record, record.backend_id.product_stock_field_id.name if record.backend_id.product_stock_field_id else "XXX", "99999"))
        return return_dict

class Shopware6ProductTemplateExporter(Component):
    _name = 'shopware6.product.template.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.product.template']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        for attribute in binding.openerp_id.attribute_line_ids:
            new_attribute_binding = binding.backend_id.create_bindings_for_model(attribute.attribute_id, 'shopware6_bind_ids')



    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        res = super(Shopware6ProductTemplateExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        """ Can do several actions after exporting a record on shopware 6"""
        print("Updated Fields.......", self.fields)
        config_setting = self.backend_adapter.get_config_setting(self.binding.shopware6_id)
        total_option = []
        for option in config_setting:
            total_option.append(option.get("attributes", {}).get("optionId", False))
        self.env.cr.execute("update product_template set config_setting=%s where id=%s;",
                            ("@".join(total_option), int(self.binding.openerp_id.id),))

        children =  self.backend_adapter.get_children(self.binding.shopware6_id)

        # #Assign Sale Channel START
        # updated_fields = self.fields
        # sales_channel_fields = ['sales_channel_ids']
        # if updated_fields is None or any(item in updated_fields for item in sales_channel_fields):
        #     odoo_channels = []
        #     for channel in self.binding.sales_channel_ids:
        #         odoo_channels.append(channel.shopware6_id)
        #     shopware_channels = self.backend_adapter.get_assign_channels(self.binding.shopware6_id)
        #     for channel in shopware_channels:
        #         if channel.get("attributes", {}).get("salesChannelId") not in odoo_channels:
        #             self.backend_adapter.del_assign_channels(channel.get("_uniqueIdentifier"))
        #         else:
        #             odoo_channels.remove(channel.get("attributes", {}).get("salesChannelId"))
        #     for channel in odoo_channels:
        #         self.backend_adapter.assign_channels(self.binding.shopware6_id,{"salesChannelId": channel, "visibility": 30})

        # Assign Sale Channel STOP
        product_template = self.binding.openerp_id

        if self.binding.openerp_id.product_variant_count != 1:
            '''
            In odoo when we change attribute odoo is archiving unwanted variant,
            thats why we need to delete those variants on shopware.
            '''
            for image in product_template.product_tmpl_media_ids:
                export_property = self.binding.backend_id.create_bindings_for_model(image, 'shopware6_bind_ids')

            shopware_children = []
            for child in children:
                shopware_children.append(child.get("id"))
            odoo_children = []
            for variant in self.binding.openerp_id.product_variant_ids:
                for binding in variant.shopware6_bind_ids:
                    odoo_children.append(binding.shopware6_id)
            for remove in [s for s in shopware_children if s not in odoo_children]:
                binder = self.binder_for('shopware6.product.product')
                product_id = binder.to_internal(remove, unwrap=True)
                product_id.shopware6_bind_ids.unlink()
                self.backend_adapter.delete(remove)
            pass

class Shopware6ProductTemplateDeleter(Component):
    _name = 'shopware6.product.template.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.product.template']
    _usage = 'record.exporter.deleter'

