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

from ...constants import ADD_ATTR_ACTION, REMOVE_ATTR_ACTION, ATTRS_ODOO_MASTER
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (only_create)
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import mapping
from . importer import PRODUCT_ATTRIBUTE_FILTERS


class ProductAttributeExportMapper(Component):
    _name = 'magento.product.attribute.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = ['magento.product.attribute']

    direct = [
        ('magento_code', 'attribute_code'),
        ('default_value', 'default_value'),
        ('attribute_scope', 'scope')
    ]

    def _prepare_attribute_storeview_data(self, record, storeview):
        lang_code = 'en_US'
        if storeview.lang_id:
            lang_code = storeview.lang_id.code

        res = {
            'name': record.with_context(lang=lang_code).name
        }

        return res

    @mapping
    def frontend_label(self, record):
        res = {'frontend_label': []}
        storeviews = self.env['magento.storeview'].search([])

        for storeview in storeviews:
            sv_data = self._prepare_attribute_storeview_data(record, storeview)

            res['frontend_label'].append({
                'store_id': storeview.magento_id,
                'label': sv_data['name']
            })

        return res

    @mapping
    def attribute_type_data(self, record):
        res = PRODUCT_ATTRIBUTE_FILTERS[record.type]
        if record.type == 'select':
            res['is_configurable'] = 0

        return res


class ProductAttributeExporter(Component):
    _name = 'magento.product.attribute.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.attribute']
    _usage = 'record.exporter'

    def _run(self, fields=None):
        print("Export attribute is called... ===> ")
        res = super(ProductAttributeExporter, self)._run(fields)
        return res

    def _after_export(self):
        '''
        for attribute_binding in self.binding_record.magento_attribute_ids.filtered(lambda rec: rec.backend_id.id == self.backend_record.id and rec.magento_id):
            self.binding_record.with_delay().adjust_attribute_on_attrset(attribute_binding.id,self.binding_record.id, ADD_ATTR_ACTION)
        '''
class MagentoProductAttributeListener(Component):
    _name = 'magento.product.attribute.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.attribute']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        return True # magento_stop
        record.with_delay().export_record()
        return True

class ProductAttributeValueExportMapper(Component):
    _name = 'magento.product.attribute.value.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = ['magento.product.attribute.value']

    direct = [
        ('name','label'),
        ('admin_name','label'),
    ]


class ProductAttributeValueExporter(Component):
    _name = 'magento.product.attribute.value.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.attribute.value']
    _usage = 'record.exporter'

    def _run(self, fields=None):
        print("Export attribute Value is called... ===> ")
        res = super(ProductAttributeValueExporter, self)._run(fields)
        return res

    def _after_export(self):
        print("After Export Attribute Value method is called ===> ",self)
        '''
        for attribute_binding in self.binding_record.magento_attribute_ids.filtered(lambda rec: rec.backend_id.id == self.backend_record.id and rec.magento_id):
            self.binding_record.with_delay().adjust_attribute_on_attrset(attribute_binding.id,self.binding_record.id, ADD_ATTR_ACTION)
        '''
class MagentoProductAttributeValue(Component):
    _name = 'magento.product.attribute.value.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.attribute.value']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        return True # magento_stop
        if record.backend_id.product_attributes_sync_type == ATTRS_ODOO_MASTER:
            record.with_delay().export_record()
        return True