# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Openfellas (http://openfellas.com) All Rights Reserved.
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

import logging
import xmlrpc.client

from collections import defaultdict

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)



class MagentoProductAttributeValue(models.Model):
    _inherit = 'magento.product.attribute.value'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ctx = self.env.context

        if ctx.get('search_warranty_attibute', False):
            args = [('magento_attribute_id.technical_name', '=', 'grimm_warranty_time')]

        if 'search_brand_from_magento_backend' in ctx:
            args = [
                ('magento_attribute_id.technical_name', '=', 'grimm_manufacturer'),
                ('backend_id', '=', ctx['search_brand_from_magento_backend'] or -1)
            ]

        if 'search_status_from_magento_backend' in ctx:
            args = [
                ('magento_attribute_id.technical_name', '=', 'status'),
                ('backend_id', '=', ctx['search_status_from_magento_backend'] or -1)
            ]

        res = super(MagentoProductAttributeValue, self).name_search(name=name, args=args, operator=operator,
                                                                    limit=limit)
        return res

'''
class MagentoBindingProductAttributeListener(Component):
    _name = 'magento.product.attribute.set.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.attribute.set']

    def on_record_write(self, record, fields=None):
        record.with_delay().export_record()

class ProductAttributeExporter(Component):
    _name = 'magento.product.attribute.set.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.attribute.set']
    _usage = 'record.exporter'

    def __init__(self, connector_env):
        super(ProductAttributeExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.link_to_parent = False
        self.fields = None

    def _should_import(self):
        return False

    def run(self, binding, fields):
        res_list = self.backend_adapter._call('product_attribute_set.create',[{'attributeSetName':'XXXGRIMXXX','skeletonSetId':30}])
        print(self.backend_adapter,"Return data is ===> ",res_list)
        return True
'''
