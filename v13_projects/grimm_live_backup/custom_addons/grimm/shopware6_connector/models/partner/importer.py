# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
from ...components.mapper import normalize_datetime
from ...exception import OrderImportRuleRetry

_logger = logging.getLogger(__name__)

class PartnerImportMapper(Component):

    _name = 'shopware6.res.partner.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = ['shopware6.res.partner']

    direct = [
        ('email', 'email'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def map_company_id(self, record):
        if self.work.collection.default_company_id:
            return {'company_id': self.work.collection.default_company_id.id}

    @mapping
    def map_leitwegId(self, record):
        return_res = {}
        attr = record.get("attributes",{})
        if isinstance(attr.get("customFields", {}),dict):
            leitwegId = attr.get("customFields", {}).get("custom_grimm_leitwegId", False)
            if leitwegId:
                return_res["leitweg_id"] = leitwegId
        return return_res

    @mapping
    def map_vat_id(self, record):
        return_res = {}
        attr = record.get("attributes",{})
        if attr.get("vatIds",False) and attr.get("vatIds",False) is not None:
            for vat in attr.get("vatIds",[]):
                return_res["vat"] = vat
        return return_res

    @mapping
    def mapping_birthday(self, record):
        return_res = {}
        attr = record.get("attributes")
        if attr.get("birthday", False):
            return_res["birthday"] = attr.get('birthday').split("T")[0]
        return return_res

    @only_create
    @mapping
    def is_company(self, record):
        # partners are companies so we can bind
        # addresses on them
        return {'is_company': True}

    @mapping
    def names(self, record):
        # TODO create a glue module for base_surname

        attr = record.get("attributes")

        parts = [part for part in (attr.get('firstName', ''),
                                   attr.get('lastName', '')) if part]
        if attr.get("company",False):
            parts = [attr.get('company', '')]
        return {'name': ' '.join(parts)}

    @mapping
    def set_email(self, record):
        attr = record.get("attributes")
        return {'email': attr.get("email")}


class PartnerAddressImportMapper(Component):

    _name = 'shopware6.address.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = ['shopware6.address']

    direct = [
        ('email', 'email'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def map_company_id(self, record):
        if self.work.collection.default_company_id:
            return {'company_id': self.work.collection.default_company_id.id}

    @mapping
    def names(self, record):
        # TODO create a glue module for base_surname
        attr = record.get("attributes")

        parts = [part for part in (attr.get('firstName', ''),
                                   attr.get('lastName', '')) if part]
        if attr.get("company",False):
            parts = [attr.get('company', '')]
        return {'name': ' '.join(parts)}

    @mapping
    def set_address(self, record):
        attr = record.get("attributes")
        res = {}
        res["street"] = attr.get('street', '')
        res["zip"] = attr.get('zipcode', '')
        res["city"] = attr.get('city', '')
        res["phone"] = attr.get('phoneNumber', '')
        if record.get("country_id", False):
            res["country_id"] = record.get("country_id", False)
        return res

    '''
    @mapping
    def set_address(self, record):
        if record.get("defaultShippingAddress"):
            return{
                "street": record.get("defaultShippingAddress").get("street"),
                "zip": record.get("defaultShippingAddress").get("zipcode"),
                "city": record.get("defaultShippingAddress").get("city"),
            }

    @mapping
    def shop_id(self, record):
        binder = self.binder_for(model='shopware6.shop')
        shop_id = binder.to_openerp(record.get('shopId',1))
        return {'shop_id': shop_id}

    @only_create
    @mapping
    def customer(self, record):
        return {'customer': True}
    '''
class ResPartnerImporter(Component):
    _name = 'shopware6.res.partner.importer'
    _inherit = 'shopware6.importer'
    _apply_on = 'shopware6.res.partner'

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        print(binding.shopware6_id, "We have successfully imported record now going to import child record.....", self.backend_adapter)
        # child_address = self.backend_adapter.get_child_address(binding.shopware6_id)
        # importer = self.component(usage='record.importer', model_name='shopware6.address')
        # for child in child_address:
        #     print("Now going to import child is ====>>>> ", child.get("id"))
        #     importer.run(child.get("id"))
        '''
        importer = self.component(usage='record.importer', model_name='shopware6.res.partner')
        create_id = importer.run('38a77dcd94d148b18580559d9b9c6f5e')
        print("Value of created ID ==> ", create_id)
        '''
        return



'''   
class SupplierImportMapper(Component):

    _name = 'shopware6.supplier.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.supplier'
    
class SupplierImporter(Component):
    _name = 'shopware6.supplier.importer'
    _inherit = 'shopware6.importer'
    _apply_on = 'shopware6.supplier'

class AddressImportMapper(Component):
    _name = 'shopware6.address.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = ['shopware6.address', 'shopware6.invoice.address']

    direct = [
        ('email', 'email'),
        ('street', 'street'),
        ('zipCode', 'zip'),
        ('city', 'city'),
    ]

    @mapping
    def set_name(self, record):
        parts = [part for part in (record['firstName'], record['lastName']) if part]
        return {'name': ' '.join(parts)}

    @mapping
    def map_company_id(self, record):
        if self.work.collection.default_company_id:
            return {'company_id': self.work.collection.default_company_id.id}

    @only_create
    @mapping
    def set_active(self, record):
        return {'active': True}

    @mapping
    def set_address(self, record):
        if record.get("defaultShippingAddress"):
            return {
                "street": record.get("defaultShippingAddress").get("street"),
                "zip": record.get("defaultShippingAddress").get("zipcode"),
                "city": record.get("defaultShippingAddress").get("city"),
            }

    @mapping
    def shop_id(self, record):
        binder = self.binder_for(model='shopware6.shop')
        shop_id = binder.to_openerp(record.get('shopId', 1))
        return {'shop_id': shop_id}

    @only_create
    @mapping
    def customer(self, record):
        return {'customer': True}
'''
class Shopware6AddressImporter(Component):
    _name = 'shopware6.address.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.address']

    def _before_import(self):
        record = self.shopware_record
        countryId = record.get("attributes", {}).get("countryId", False)
        if countryId:
            country_data = self.backend_adapter.get_country(countryId)
            country_code = country_data.get("attributes", {}).get("iso", False)
            if country_code:
                exist_country = self.env['res.country'].search([('code', '=',country_code)],limit=1,)
                if exist_country:
                    record["country_id"] = exist_country.id
