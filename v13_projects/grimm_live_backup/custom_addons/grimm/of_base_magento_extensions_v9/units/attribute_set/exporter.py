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


class ProductAttributeSetExportMapper(Component):
    _name = 'magento.product.attribute.set.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = ['magento.product.attribute.set']

    direct = [
        ('name', 'name'),
    ]

    @only_create
    @mapping
    def skeleton_attribute_set(self, record):
        base_attr_set = record.skeleton_attribute_set_id
        for attr_set_binding in base_attr_set.magento_binding_ids.filtered(
                lambda rec: rec.magento_id and rec.backend_id.id == record.backend_id.id):
            return {'skeleton_set_id': attr_set_binding.magento_id}


class ProductAttributeSetExporter(Component):
    _name = 'magento.product.attribute.set.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.attribute.set']
    _usage = 'record.exporter'

    def _should_import(self):
        return False

    def add_attribute_to_set(self, attribute_binding, attribute_set_binding):
        assert attribute_binding.magento_id and attribute_set_binding.magento_id
        res = self.backend_adapter.assign_attribute_to_set(attribute_binding.magento_id,
                                                           attribute_set_binding.magento_id)
        return res

    def remove_attribute_from_set(self, attribute_binding, attribute_set_binding):
        assert attribute_binding.magento_id and attribute_set_binding.magento_id
        res = self.backend_adapter.remove_attribute_from_set(attribute_binding.magento_id,
                                                             attribute_set_binding.magento_id)
        return res

    def adjust_attribute_on_set(self, attribute_binding_id, attribute_set_binding_id, action):
        assert action in (ADD_ATTR_ACTION, REMOVE_ATTR_ACTION)

        attribute_binding = self.env['magento.product.attribute'].browse(attribute_binding_id)
        attribute_set_binding = self.env['magento.product.attribute.set'].browse(attribute_set_binding_id)
        res = None
        if action == ADD_ATTR_ACTION:
            res = self.add_attribute_to_set(attribute_binding, attribute_set_binding)
        elif action == REMOVE_ATTR_ACTION:
            res = self.remove_attribute_from_set(attribute_binding, attribute_set_binding)

        return res

    def _run(self, fields=None):
        self.initial_export = False
        if not self.magento_id:
            self.initial_export = True

        res = super(ProductAttributeSetExporter, self)._run(fields)
        return res

    def _after_export(self):
        if self.initial_export:
            '''
            for attribute_binding in self.binding_record.magento_attribute_ids.filtered(lambda rec: rec.backend_id.id == self.backend_record.id and rec.magento_id):
                self.binding_record.with_delay().adjust_attribute_on_attrset(attribute_binding.id,self.binding_record.id, ADD_ATTR_ACTION)
            '''

class MagentoProductListener(Component):
    _name = 'magento.product.attribute.set.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.attribute.set']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        return True # magento_stop
        if record.backend_id.product_attributes_sync_type == ATTRS_ODOO_MASTER:
            record.with_delay().export_record()
        return True

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        return True # magento_stop
        fields_to_consider = record.fields_to_update_on_magento()

        if fields:
            fields_to_update = list(set(fields.keys()).intersection(fields_to_consider))

            if len(fields_to_update) > 0:
                attribute_ids_to_remove = []
                attribute_ids_to_assign = []

                attribute_ids_before_update = self._context.get('attribute_ids_before_update', False)
                if attribute_ids_before_update:
                    current_attribute_ids = record.product_attribute_ids.ids
                    attribute_ids_to_remove = list(set(attribute_ids_before_update) - set(current_attribute_ids))
                    attribute_ids_to_assign = list(set(current_attribute_ids) - set(attribute_ids_before_update))

                for binding in record.magento_binding_ids:
                    if binding.magento_id and binding.backend_id.product_attributes_sync_type == ATTRS_ODOO_MASTER:
                        record.with_delay().export_record()

                        if len(attribute_ids_to_remove) > 0:
                            attributes_to_remove = self.env['product.attribute'].search(
                                [('id', 'in', attribute_ids_to_remove)])

                            for attr in attributes_to_remove:
                                for attr_binding in attr.magento_binding_ids.filtered(
                                        lambda rec: rec.magento_id and rec.backend_id.id == binding.backend_id.id):
                                    record.with_delay().adjust_attribute_on_attrset(attr_binding.id,
                                                                                    binding.id,
                                                                                    REMOVE_ATTR_ACTION)

                        if len(attribute_ids_to_assign) > 0:
                            attributes_to_assign = self.env['product.attribute'].search(
                                [('id', 'in', attribute_ids_to_assign)])
                            for attr in attributes_to_assign:
                                for attr_binding in attr.magento_binding_ids.filtered(
                                        lambda rec: rec.magento_id and rec.backend_id.id == binding.backend_id.id):
                                    record.with_delay().adjust_attribute_on_attrset(attr_binding.id,
                                                                                    binding.id,
                                                                                    ADD_ATTR_ACTION)

        return True
