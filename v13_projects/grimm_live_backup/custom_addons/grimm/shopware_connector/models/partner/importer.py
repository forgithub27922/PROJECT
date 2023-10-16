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

    _name = 'shopware.res.partner.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.res.partner'

    direct = [
        ('email', 'email'),
        #('dob', 'birthday'),
        (normalize_datetime('changed'), 'create_date'),
        (normalize_datetime('changed'), 'write_date'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def set_company_name(self, record):
        default_address = record.get("defaultBillingAddress",{})
        company_name = default_address.get("company",False)
        if company_name:
            return {'company': company_name}
        return {}

    @mapping
    def map_company_id(self, record):
        return {} # Setting company null
        if self.work.collection.default_company_id:
            return {'company_id': self.work.collection.default_company_id.id}

    @only_create
    @mapping
    def is_company(self, record):
        # partners are companies so we can bind
        # addresses on them
        return {'is_company': True}

    @mapping
    def names(self, record):
        # TODO create a glue module for base_surname
        parts = [part for part in (record['firstname'],
                                   record['lastname']) if part]
        return {'name': ' '.join(parts)}

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
        binder = self.binder_for(model='shopware.shop')
        shop_id = binder.to_openerp(record.get('shopId',1))
        return {'shop_id': shop_id}

    @only_create
    @mapping
    def customer(self, record):
        return {'customer': True}

class SupplierImportMapper(Component):

    _name = 'shopware.supplier.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.supplier'



class ResPartnerImporter(Component):
    _name = 'shopware.res.partner.importer'
    _inherit = 'shopware.importer'
    _apply_on = 'shopware.res.partner'

class SupplierImporter(Component):
    _name = 'shopware.supplier.importer'
    _inherit = 'shopware.importer'
    _apply_on = 'shopware.supplier'

class AddressImportMapper(Component):
    _name = 'shopware.address.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = ['shopware.address', 'shopware.invoice.address']

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
    def set_company_name(self, record):
        company_name = record.get("company", False)
        if company_name:
            return {'company': company_name}
        return {}

    @mapping
    def map_company_id(self, record):
        return {}
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
        binder = self.binder_for(model='shopware.shop')
        shop_id = binder.to_openerp(record.get('shopId', 1))
        return {'shop_id': shop_id}

    @only_create
    @mapping
    def customer(self, record):
        return {'customer': True}

class ShopwareAddressImporter(Component):
    _name = 'shopware.address.importer'
    _inherit = 'shopware.importer'
    _apply_on = ['shopware.address','shopware.invoice.address']