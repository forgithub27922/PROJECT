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


from ...constants import CONFIGURABLE_TYPE, SELECT_TYPE, TEXT_TYPE, SIMPLE_TEXT_TYPE, GLOBAL_SCOPE, PRICE_TYPE, \
    MULTISELECT_TYPE, DATE_TYPE, BOOLEAN_TYPE, WEIGHT_TYPE, EMPTY_TYPE
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

import logging

_logger = logging.getLogger(__name__)

PRODUCT_ATTRIBUTE_FILTERS = {
    CONFIGURABLE_TYPE: {
        'frontend_input': SELECT_TYPE,
        'is_configurable': '1',
        'scope': GLOBAL_SCOPE
    },
    SELECT_TYPE: {
        'frontend_input': SELECT_TYPE
    },
    TEXT_TYPE: {
        'frontend_input': 'textarea'
    },
    SIMPLE_TEXT_TYPE: {
        'frontend_input': 'text'
    },
    MULTISELECT_TYPE: {
        'frontend_input': MULTISELECT_TYPE
    },
    PRICE_TYPE: {
        'frontend_input': PRICE_TYPE
    },
    DATE_TYPE: {
        'frontend_input': DATE_TYPE
    },
    BOOLEAN_TYPE: {
        'frontend_input': BOOLEAN_TYPE
    },
    WEIGHT_TYPE: {
        'frontend_input': WEIGHT_TYPE
    },
    EMPTY_TYPE: {
        'frontend_input': EMPTY_TYPE
    }
}


def filters_match(attribute_filters, magento_data):
    res = True

    for key in list(attribute_filters.keys()):
        if isinstance(attribute_filters[key], list) and isinstance(magento_data[key], list):
            condition = set(attribute_filters[key]) <= set(magento_data[key])
        else:
            condition = attribute_filters[key] == magento_data.get(key, None)

        if not condition:
            res = False
            break

    return res


class ProductAttributeImportMapper(Component):
    _name = 'magento.product.attribute.import.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = ['magento.product.attribute']

    direct = [
        ('attribute_code', 'magento_code'),
        ('attribute_code', 'technical_name'),
        ('default_value', 'default_value'),
    ]

    @mapping
    def is_visible_on_front(self, record):
        try:
            is_visible_on_front = bool(int(record.get('is_visible_on_front', False)))
        except:
            is_visible_on_front = False
        return {'is_visible_on_front': is_visible_on_front}

    @mapping
    def is_global(self, record):
        try:
            is_global = bool(int(record.get('is_global', False)))
        except:
            is_global = False
        return {'is_global': is_global}

    @mapping
    def is_required(self, record):
        is_required = record.get('is_required', False)
        if is_required:
            try:
                is_required = bool(int(is_required))
            except:
                is_required = False
        return {'is_required': is_required}

    @mapping
    def is_configurable(self, record):
        if filters_match(PRODUCT_ATTRIBUTE_FILTERS['configurable'], record):
            return {
                'is_configurable': True,
                'type': CONFIGURABLE_TYPE,
                'variant_attribute': True
            }

        attr_type = None

        for f in list(PRODUCT_ATTRIBUTE_FILTERS.keys()):
            if filters_match(PRODUCT_ATTRIBUTE_FILTERS[f], record):
                attr_type = f
                break

        return {
            'is_configurable': False,
            'type': attr_type if attr_type else 'select',
            'variant_attribute': False
        }

    @mapping
    def default_value(self, record):
        res = {}

        if 'default_value' in record and record['default_value'] and record['default_value'] != '0':

            if record['frontend_input'] == 'date':
                import time
                epoch = int(record['default_value'])
                res['default_value'] = time.strftime('%Y-%m-%d', time.localtime(epoch))
            else:
                res['default_value'] = record['default_value']

        return res

    @mapping
    def name(self, record):
        if self.backend_record.attrs_default_storeview_id:
            self.options.current_storeview_id = self.backend_record.attrs_default_storeview_id.magento_id
        labels = record.get('frontend_label', [])
        label = None

        storeview_ids = [self.options.current_storeview_id, self.backend_record.admin_storeview_id.magento_id]

        for lbl in labels:
            if not label:
                label = lbl['label']

            for sv_id in storeview_ids:
                if sv_id and str(lbl['store_id']).strip() == str(sv_id).strip():
                    label = lbl['label']
                    break

        if not label:
            label = record['attribute_code']

        return {
            'name': label
        }

    @mapping
    def scope(self, record):
        res = {}
        if record.get('scope', False):
            res['attribute_scope'] = record['scope']
        else:
            res['scope'] = GLOBAL_SCOPE

        return res

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ProductAttributeValueImportMapper(Component):
    _name = 'magento.product.attribute.value.import.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = ['magento.product.attribute.value']

    direct = [
        ('label', 'name'),
        ('label', 'admin_name'),
    ]

    @mapping
    def backend_id(self, record):
        return {
            'backend_id': self.backend_record.id
        }

    @mapping
    def magento_id(self, record):
        res = {}
        if 'value' in record:
            res['magento_id'] = str(record['value'])

        return res

    @mapping
    def attribute_id(self, record):
        res = {}
        magento_attribute_id = record.get('attribute_id', False)

        if magento_attribute_id:
            attr_binder = self.binder_for('magento.product.attribute')
            magento_attribute = self.env['magento.product.attribute'].search(
                [('magento_id', '=', magento_attribute_id)])
            if not magento_attribute:
                res['attribute_id'] = None
            else:
                attribute_id = attr_binder.to_openerp(magento_attribute.id, unwrap=True)
                res['attribute_id'] = attribute_id

        return res


class ProductAttributeImport(Component):
    _name = 'magento.product.attribute.importer'
    _inherit = 'magento.importer'
    _apply_on = ['magento.product.attribute']
    _model_name = ['magento.product.attribute']

    _allowed_attribute_types = ['select', 'textarea', 'text']

    def run(self, magento_id, magento_set_ids, force=False):
        self.magento_set_ids = magento_set_ids
        return super(ProductAttributeImport, self).run(magento_id, force=force)

    def _must_skip(self):

        magento_attr_type = self.magento_record['frontend_input']
        odoo_attr_type = self.backend_record.import_attributes_of_type

        must_skip = False

        if odoo_attr_type:
            must_skip = not (PRODUCT_ATTRIBUTE_FILTERS[odoo_attr_type]['frontend_input'] == magento_attr_type and
                             magento_attr_type in self._allowed_attribute_types and
                             filters_match(PRODUCT_ATTRIBUTE_FILTERS[odoo_attr_type], self.magento_record))
        """
        else:
            must_skip = magento_attr_type not in self._allowed_attribute_types
        """

        if must_skip:
            return must_skip

        return super(ProductAttributeImport, self)._must_skip()

    def _collect_options_storeview_vals(self, binding):
        if not binding.magento_id:
            return {}

        storeviews = self.env['magento.storeview'].search([('backend_id', '=', self.backend_record.id)])
        default_lang = self.backend_record.default_lang_id
        lang_storeviews = [sv for sv in storeviews if sv.lang_id and sv.lang_id != default_lang]

        values_data_per_sv = {}
        for sv in lang_storeviews:
            val_data = self.backend_adapter.get_options(binding.magento_id, sv.magento_id)
            values_data_per_sv[sv.magento_id] = val_data

        return values_data_per_sv

    def _adjust_attribute_options(self, binding):

        values_to_add = []
        values_to_update = {}
        magento_options = self.magento_record.get('options', [])

        if magento_options:
            attr_value_mapper = self.component(usage='import.mapper', model_name='magento.product.attribute.value')
            attribute_values = self.env['magento.product.attribute.value'].search(
                [('attribute_id', '=', binding.openerp_id.id), '|', ('active', '=', False), ('active', '=', True)])

            if attribute_values:
                attribute_values.with_context(connector_no_export=True).write({'active': False})

            for option in magento_options:
                already_exists = False

                for attr_value in attribute_values:
                    if attr_value.magento_id == option['value']:
                        already_exists = True
                        attr_value.with_context(connector_no_export=True).write({'active': True})

                        if attr_value.admin_name != option['label'] or attr_value.name != option['label']:
                            values_to_update[attr_value.id] = {'admin_name': option['label'], 'name': option['label']}

                        break
                    if attr_value.name == option['label']:
                        already_exists = True
                        attr_value.with_context(connector_no_export=True).write({'active': True})
                        values_to_update[attr_value.id] = {'magento_id': option['value']}
                        break

                if not already_exists:
                    # record = map_record.values()
                    #
                    # data = dict((field, value) for field, value in record.iteritems()
                    #             if field in translatable_fields)
                    #
                    new_attr_data = (attr_value_mapper.map_record(option).values())
                    new_attr_data['attribute_id'] = binding.openerp_id.id
                    values_to_add.append(new_attr_data)

            for value_data in values_to_add:
                try:
                    self.env['magento.product.attribute.value'].with_context(connector_no_export=True).create(
                        value_data)
                except:
                    _logger.error("Can't create attribute value %s for Attribute-ID %s", value_data,
                                  binding.openerp_id.id)
                    raise

            for value_id in list(values_to_update.keys()):
                value = self.env['magento.product.attribute.value'].browse(value_id)
                try:
                    value.with_context(connector_no_export=True).write(values_to_update[value.id])
                except:
                    _logger.error("Can't update attribute value %s for ID %s", values_to_update[value.id], value_id)
                    raise

        return True

    def _after_import(self, binding):
        if binding.type in (CONFIGURABLE_TYPE, SELECT_TYPE, MULTISELECT_TYPE):
            self._adjust_attribute_options(binding)

        # self._adjust_translations(binding)

        for set_id in self.magento_set_ids:
            attr_set_binding = self.env['magento.product.attribute.set'].browse(set_id)

            if attr_set_binding is not None:
                vals = {'product_attribute_ids': [(4, binding.openerp_id.id)]}
                attr_set_binding.with_context(connector_no_export=True).write(vals)

        return super(ProductAttributeImport, self)._after_import(binding.id)


class ProductAttributeSetBatchImport(Component):
    _name = 'magento.product.attribute.batch.importer'
    _inherit = 'magento.delayed.batch.importer'
    _apply_on = ['magento.product.attribute']

    def run(self, magento_attribute_set, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(magento_attribute_set.magento_id)
        for record_id in record_ids:
            self._import_record(record_id, magento_attribute_set.ids)

    def _import_record(self, magento_id, magento_attribute_set_ids, job_options=None, **kwargs):
        """ Delay the import of the records"""
        delayable = self.model.with_delay(**job_options or {})
        delayable.import_record(self.backend_record, magento_id, magento_attribute_set_ids, **kwargs)

# @openfellas_magento_extensions
# class ProductAttributeBatchImport(DelayedBatchImport):
#     _model_name = ['magento.product.attribute']
#
#     def _import_record(self, record_id, magento_set_ids, **kwargs):
#         attribute_import_record.delay(
#             self.session, self.model._name, self.backend_record.id, record_id,
#             magento_set_ids, **kwargs
#         )
#
#     def run(self, magento_set_id):
#         attributes_data = {}
#         attribute_sets = None
#         counter = 0
#
#         _logger.info('Started batch import of product attributes')
#
#         if not magento_set_id:
#             magento_attribute_sets = self.env['magento.product.attribute.set'].search([])
#         else:
#             magento_attribute_sets = self.env['magento.product.attribute.set'].browse(magento_set_id)
#
#         _logger.info('Found %s magento attribute sets in odoo' % (len(magento_attribute_sets)))
#         number = len(magento_attribute_sets)
#
#         cleanup_query = """DELETE FROM product_attr_set_product_attr_rel rel
#                            USING product_attribute atr
#                            WHERE rel.attr_id=atr.id AND rel.attr_set_id=%s"""
#
#         if self.backend_record.import_attributes_of_type:
#             cleanup_query += """ AND atr.type='%s'""" % (self.backend_record.import_attributes_of_type,)
#
#         for attr_set in magento_attribute_sets:
#             counter += 1
#
#             _logger.info(
#                 '[%s / %s] Searching for attributes on Magento for attribute set %s' % (counter, number, attr_set.name))
#             magento_attribute_ids = self.backend_adapter.search(attr_set.magento_id)
#
#             for attr_id in magento_attribute_ids:
#                 if attr_id in attributes_data:
#                     attributes_data[attr_id].append(attr_set.id)
#                 else:
#                     attributes_data[attr_id] = [attr_set.id]
#
#             self.env.cr.execute(cleanup_query % (attr_set.openerp_id.id,))
#
#         for attr_id in list(attributes_data.keys()):
#             self._import_record(attr_id, attributes_data[attr_id])
#
#
# @job(default_channel='root.magento')
# def attribute_import_record(session, model_name, backend_id, magento_id, magento_set_ids):
#     """ Import product attribute from Magento """
#
#     env = get_environment(session, model_name, backend_id)
#     importer = env.get_connector_unit(ProductAttributeImport)
#     importer.run(magento_id, magento_set_ids)
#
#
# @job(default_channel='root.magento')
# def prepare_batch_attribute_import(session, model_name, backend_id, magento_set_id=None):
#     """ Prepare import of product attributes from Magento """
#
#     env = get_environment(session, model_name, backend_id)
#     batch_importer = env.get_connector_unit(ProductAttributeBatchImport)
#     batch_importer.run(magento_set_id)
