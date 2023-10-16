# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from datetime import datetime
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
import logging
_logger = logging.getLogger(__name__)

class ProductProductExportMapperShopware6(Component):
    _name = 'shopware6.product.product.export.mapper'
    _inherit = 'shopware6.export.mapper'
    _apply_on = ['shopware6.product.product']

    direct = [
        ('name', 'name'),
        ('shopware_active', 'active')
    ]

    @changed_by('default_code', 'description')
    @mapping
    def assign_miscellaneous_field(self, record):
        return_dict = {}
        return_dict["productNumber"] = record.default_code if record.default_code else str(record.openerp_id.id)
        return_dict["description"] = "" if record.description == '<p><br></p>' or record.description == '' else record.description
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
                # return_dict["swagCustomizedProductsTemplateId"] = "5793e2c3052b488994f1168dd41acd9f"
                break
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

    @changed_by('attribute_line_ids')
    @mapping
    def assign_variant_options(self, record):
        return_dict = {}
        option_list = []
        for attribute in record.product_template_attribute_value_ids:
            for bind in attribute.product_attribute_value_id.shopware6_bind_ids:
                option_list.append({"id": bind.shopware6_id})

        if option_list:
            return_dict["options"] = option_list
            return return_dict
        return return_dict

    @mapping
    def assign_price(self, record):
        currency_id = record.backend_id.shopware6_currency_id
        return {"price": [
            {
                "currencyId": currency_id,
                "net": record.lst_price,
                "gross": record.lst_price,
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


    @mapping
    def set_parent(self, record):
        return_dict = {}
        # return_dict['parentId'] = 'd21b835d5dc546cb9baa3148eee9a435'
        # return return_dict
        if record.product_tmpl_id.product_variant_count > 1:
            if record.product_tmpl_id.shopware6_pt_bind_ids:
                if record.product_tmpl_id.shopware6_pt_bind_ids[0].shopware6_id:
                    return_dict['parentId'] = record.product_tmpl_id.shopware6_pt_bind_ids[0].shopware6_id
        return return_dict

class Shopware6ProductProductExporter(Component):
    _name = 'shopware6.product.product.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.product.product']
    _usage = 'record.exporter'


    def _export_dependency(self,binding):
        # print("\n\n\n\n***********************************\n\nGoing to export dependancy for product.product...")
        # product_template = binding.openerp_id.product_tmpl_id
        # product_product = binding.openerp_id
        #
        # if product_template.product_variant_count != 1:
        #     for bind in product_template.shopware6_pt_bind_ids:
        #         bind.export_record()



        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = args[0] if args else []
        if kwargs and kwargs.get("data_option"):
            rec_ids = kwargs.get("data_option").get("rec_ids", [])
            rec_id_fields = kwargs.get("data_option").get("rec_id_fields", {})
            product_adapter = self.component(usage='backend.adapter', model_name='shopware6.product.product')
            product_bindings = self.env["shopware6.product.product"].browse(rec_ids)
            product_mapper = self.component(usage='export.mapper', model_name='shopware6.product.product')
            if rec_ids:
                total_payload = []
                for binding in product_bindings:
                    res = {}
                    map_product = product_mapper.map_record(binding)
                    res = map_product.values(fields=rec_id_fields.get(str(binding.id),[]))
                    #res.update(product_mapper.assign_price(binding))
                    res["id"] = binding.shopware6_id
                    total_payload.append(res)
                try:
                    mass_update = product_adapter.mass_update_product(
                        [{"action": "upsert", "entity": "product", "payload": total_payload}])
                except:
                    # If mass update failed due to any wrong id we will send one by one. OD-1415
                    # (Enhancement of the shopware6 API related to mass update. If a mass update
                    # fails. Odoo needs to send them one by one.)
                    failed = []
                    for tp in total_payload:
                        try:
                            mass_update = product_adapter.mass_update_product([{"action": "upsert", "entity": "product", "payload": [tp]}])
                        except:
                            failed.append(tp.get("id",""))
                    return "Except %s id(s) record has been synced"%failed


                return mass_update

        res = super(Shopware6ProductProductExporter, self).run(binding_id, *args, **kwargs)

        return res

    def _after_export(self):
        product_product = self.binding.openerp_id

        #After export read same record
        # product_version_id = self.backend_adapter.read(self.binding.shopware6_id, "?includes[product][]=versionId")
        # print("===========================================================GOING to update shopware6_version_id ===> ", product_version_id, self.binding.openerp_id)
        # print("Goint to update ===> ","update product_product set shopware6_version_id=%s where id=%s;",(product_version_id.get("versionId"), int(self.binding.openerp_id.id),))
        # self.env.cr.execute("update product_product set shopware6_version_id=%s where id=%s;",(product_version_id.get("versionId"), int(self.binding.openerp_id.id),))


        # self.fields = [] if self.fields is None else self.fields
        # print("========================FIELDS=====================>>>>> ", self.fields)
        # if 'product_media_ids' in self.fields or len(self.fields) == 0:

        # for image in product_product.product_media_ids:
        #     export_property = self.binding.backend_id.create_bindings_for_model(image, 'shopware6_bind_ids')

        # Assign Sale Channel START
        #if 'sales_channel_ids' in self.fields or len(self.fields) == 0:
        # updated_fields = self.fields
        # sales_channel_fields = ['sales_channel_ids']
        # if updated_fields is None or any(item in updated_fields for item in sales_channel_fields):
        #     odoo_channels = []
        #     for channel in self.binding.sales_channel_ids:
        #         odoo_channels.append(channel.shopware6_id)
        #
        #     shopware_channels = self.backend_adapter.get_assign_channels(self.binding.shopware6_id)
        #     for channel in shopware_channels:
        #         if channel.get("salesChannelId") not in odoo_channels:
        #             self.backend_adapter.del_assign_channels(channel.get("id"))
        #         else:
        #             odoo_channels.remove(channel.get("salesChannelId"))
        #     for channel in odoo_channels:
        #         self.backend_adapter.assign_channels(self.binding.shopware6_id,{"salesChannelId":channel,"visibility":30})

        # Assign Sale Channel STOP

        # Grimm assign cover photo start

        # for product_media in self.binding.product_media_ids:
        #     self.backend_adapter.write(self.binding.shopware6_id,{"coverId": product_media.shopware6_bind_ids[0].shopware6_id})
        # return True


    # def _after_export(self):
    #     '''
    #     This method will again execute read method for same product because we need image link ID from shopware6
    #     so product will not add images with every request.
    #     :return:
    #     '''
    #     product_data = self.backend_adapter.read(int(self.binding.shopware6_id))
    #     image_data = product_data.get('images', False)
    #     self.binding.created_at = product_data.get('added', '').replace("T", " ")
    #     self.binding.updated_at = product_data.get('changed', '').replace("T", " ")
    #     image_link = {}
    #     for image in image_data:
    #         image_link[str(image.get('mediaId'))] = {"id": image.get('id'), "articleId": image.get('articleId')}
    #     product_id = self.binding.openerp_id
    #     for image in product_id.shopware_image_ids:
    #         if not image.shopware6_id or not product_id.is_shopware_exported:
    #             for media in image.shopware_bind_ids:
    #                 if image_link.get(media.shopware6_id):
    #                     if int(self.binding.shopware6_id) == int(image_link.get(media.shopware6_id).get("articleId")):
    #                         #instead of ORM update executed direct SQL otherwise odoo connector will send this product to update on shopware6 due to on_record_write call
    #                         self.env.cr.execute("update odoo_product_image set shopware6_id=%s where id=%s;",(int(image_link.get(media.shopware6_id).get("id")),int(image.id),))
    #
    #
    #     #self.env['shopware6.image.info'].import_record(self.env['shopware6.backend'].search([]),int(self.binding.shopware6_id))

class ProductProductDeleterShopware6(Component):
    _name = 'shopware6.product.product.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.product.product']
    _usage = 'record.exporter.deleter'