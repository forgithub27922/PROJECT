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

from ..backend import openfellas_magento_extensions
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.event import on_record_write, on_record_create, on_record_unlink
from openerp.addons.connector.unit.mapper import (mapping, ExportMapper)
from openerp.addons.magentoerpconnect.unit.export_synchronizer import MagentoExporter, export_record
from ..connector_env import get_environment
from .product_attribute_import import PRODUCT_ATTRIBUTE_FILTERS
from ..constants import ATTRS_ODOO_MASTER, CONFIGURABLE_TYPE, SELECT_TYPE

@openfellas_magento_extensions
class ProductAttributeExportMapper(ExportMapper):
    _model_name = 'magento.product.attribute'

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
            'name':record.with_context(lang=lang_code).name
        }

        return res

    @mapping
    def frontend_label(self, record):
        res = {'frontend_label':[]}
        storeviews = self.env['magento.storeview'].search([])

        for storeview in storeviews:
            sv_data = self._prepare_attribute_storeview_data(record, storeview)

            res['frontend_label'].append({
                'store_id':storeview.magento_id,
                'label':sv_data['name']
            })

        return res

    @mapping
    def attribute_type_data(self, record):
        res = PRODUCT_ATTRIBUTE_FILTERS[record.type]
        if record.type=='select':
            res['is_configurable'] = 0

        return res

@openfellas_magento_extensions
class ProductAttributeExporter(MagentoExporter):
    _model_name = 'magento.product.attribute'

    def _should_import(self):
        return False

    def _prepare_option_storeview_values(self, storeview, value_binding):
        res = {}

        if storeview.code=='admin':
            option_name = value_binding.admin_name
        else:
            lang_code = 'en_US'
            if storeview.lang_id: lang_code = storeview.lang_id.code
            option_name = value_binding.with_context(lang=lang_code).name

        res['name'] = option_name

        return res

    def _prepare_new_option_data(self, value_binding):
        res_data = []
        storeviews = self.env['magento.storeview'].search([])

        for sv in storeviews:
            sv_values = self._prepare_option_storeview_values(sv, value_binding)

            res_data.append({
                'store_id':sv.magento_id,
                'value':sv_values['name']
            })

        res = {
            'label':res_data
        }

        return res

    def _add_option_to_attribute_on_magento(self, value_binding):
        option_data = self._prepare_new_option_data(value_binding)
        res = self.backend_adapter.assign_option_to_attribute(value_binding.magento_attribute_id.magento_id, option_data)
        value_binding.write({'magento_id':res})
        return res

    def _remove_option_from_attribute_on_magento(self, attribute_magento_id, value_magento_id):
        res = self.backend_adapter.remove_option_from_attribute(attribute_magento_id, value_magento_id)
        return res

    def _run(self, fields=None):
        self.initial_export = False
        if not self.magento_id:
            self.initial_export = True

        res = super(ProductAttributeExporter, self)._run(fields)
        return res

    def _after_export(self):
        if self.initial_export and self.binding_record.type in (SELECT_TYPE, CONFIGURABLE_TYPE):
            session = ConnectorSession(self.session.cr, self.session.uid, context=self.session.context)

            for value_binding in self.binding_record.magento_attribute_value_ids:
                add_option_to_attribute.delay(session, value_binding._name, value_binding.id)

@job(default_channel='root.magento')
def add_option_to_attribute(session, model_name, option_binding_id):
    """Adjust options on product attribute"""

    option_binding = session.env[model_name].browse(option_binding_id)
    env = get_environment(session, 'magento.product.attribute', option_binding.backend_id.id)
    attribute_exporter = env.get_connector_unit(ProductAttributeExporter)
    res = attribute_exporter._add_option_to_attribute_on_magento(option_binding)
    return res

@job(default_channel='root.magento')
def remove_option_from_attribute(session, model_name, backend_id, attribute_magento_id, option_magento_id):
    """Adjust options on product attribute"""

    env = get_environment(session, 'magento.product.attribute', backend_id)
    attribute_exporter = env.get_connector_unit(ProductAttributeExporter)
    res = attribute_exporter._remove_option_from_attribute_on_magento(attribute_magento_id, option_magento_id)
    return res

@on_record_create(model_names='magento.product.attribute')
def export_product_attribute_delay(session, model_name, record_id, fields=None):
    record = session.env[model_name].browse(record_id)
    if record.backend_id.product_attributes_sync_type==ATTRS_ODOO_MASTER:
        export_record.delay(session, model_name, record.id, fields=fields)

    return True

@on_record_write(model_names='product.attribute')
def update_product_attribute_delay(session, model_name, record_id, fields=None):
    record = session.env[model_name].browse(record_id)
    fields_to_consider = session.env['magento.product.attribute'].fields_to_update_on_magento()

    if fields:
        fields_to_update = list(set(fields.keys()).intersection(fields_to_consider))

        if len(fields_to_update)>0:
            for binding in record.magento_binding_ids:
                if binding.magento_id and binding.backend_id.product_attributes_sync_type==ATTRS_ODOO_MASTER:
                    export_record.delay(session, binding._name, binding.id, fields=fields_to_update)

    return True

@on_record_create(model_names='magento.product.attribute.value')
def add_attribute_options_delay(session, model_name, record_id, fields=None):
    record = session.env[model_name].browse(record_id)
    if record.magento_attribute_id.magento_id and \
        record.magento_attribute_id.type in (SELECT_TYPE, CONFIGURABLE_TYPE) and \
                    record.backend_id.product_attributes_sync_type==ATTRS_ODOO_MASTER:

        add_option_to_attribute.delay(session, model_name, record.id)

    return True

@on_record_unlink(model_names='product.attribute.value')
def remove_attribute_options_delay(session, model_name, record_id, fields=None):
    record = session.env[model_name].browse(record_id)

    for binding in record.magento_binding_ids:
        if binding.magento_attribute_id.magento_id and binding.magento_id and binding.backend_id.product_attributes_sync_type==ATTRS_ODOO_MASTER:
            remove_option_from_attribute.delay(session, 'magento.product.attribute', binding.backend_id.id, binding.magento_attribute_id.magento_id, binding.magento_id)

    return True