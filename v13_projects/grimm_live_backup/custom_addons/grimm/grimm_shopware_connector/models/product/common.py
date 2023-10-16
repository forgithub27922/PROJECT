# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client

from collections import defaultdict

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ProductProductAdapter(Component):
    _name = 'shopware.product.template.adapter'
    _inherit = 'shopware.product.template.adapter'
    _apply_on = 'shopware.product.template'

    _shopware_uri = 'articles/'


    def remove_product_link(self, relation_id):
        return self._call('delete', 'ExtendCrossSelling/%s' % (relation_id), [{}])

    def search_product_link(self, product_id):
        return_response = self._call('get', 'ExtendCrossSelling/%s' % (product_id), [{}])
        return_list = []
        for resp in return_response:
            temp_dict = {}
            temp_dict["id"] = resp.get("id")
            temp_dict["product_id"] = resp.get("articleId")
            temp_dict["rel_product_id"] = resp.get("relatedArticleId")
            temp_dict["code"] = resp.get("assignment").get("code")
            return_list.append(temp_dict)
        return return_list

    def assign_product_link(self, link_dict):
        return self._call('post', "ExtendCrossSelling/", link_dict)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopware_accessory_ids = fields.Many2many(
        'product.template', 'product_shopware_accessory_rel', 'src_id', 'dest_id', string='Shopware Accessories')

    shopware_package_content = fields.Integer("Package Content", default=1)
    shopware_basic_unit = fields.Integer("Basic Unit", default=1)
    shopware_packaging_unit = fields.Char("Packaging Unit")
    genuine = fields.Char("Genuine")
    spare_part_option = fields.Selection(
        [('Original Equipment', 'Original Equipment'), ('Recommended', 'Recommended'), ('Low Cost', 'Low Cost')],
        string='Spare Part Option', default='Original Equipment')

    @api.model
    def export_today_product(self):
        query = "select id from product_template where active='t' and product_brand_id is not null and status_on_shopware='t' and id in (select prod_id from product_taxes_rel where tax_id in (select id from account_tax where company_id=3)) and id not in (select openerp_id from shopware_product_template)"
        self._cr.execute(query)
        product_ids =[i[0] for i in self._cr.fetchall()]
        for prod_id in product_ids:
            prod_data = self.env["product.template"].browse(prod_id)
            prod_data.export_multi_to_shopware_xmlrpc()
