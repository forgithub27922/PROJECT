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

from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import Warning
from odoo.tools.translate import _

from ..constants import CONFIGURABLE_TYPE, SELECT_TYPE, TEXT_TYPE, SIMPLE_TEXT_TYPE, GLOBAL_SCOPE, STOREVIEW_SCOPE, \
    WEBSITE_SCOPE, \
    ATTRS_ODOO_MASTER, DATE_TYPE, PRICE_TYPE, BOOLEAN_TYPE, MULTISELECT_TYPE, WEIGHT_TYPE, EMPTY_TYPE

PRODUCT_ATTRIBUTE_TYPES = [
    (CONFIGURABLE_TYPE, 'Configurable'),
    (SELECT_TYPE, 'Dropdown'),
    (SIMPLE_TEXT_TYPE, 'Text'),
    (TEXT_TYPE, 'Text Area'),
    (DATE_TYPE, 'Date'),
    (PRICE_TYPE, 'Price'),
    (BOOLEAN_TYPE, 'Boolean'),
    (MULTISELECT_TYPE, 'Multiselect'),
    (WEIGHT_TYPE, 'Weight'),
    (EMPTY_TYPE, 'Empty')
]

PRODUCT_ATTRIBUTE_SCOPES = [
    (GLOBAL_SCOPE, 'Global'),
    (STOREVIEW_SCOPE, 'Storeview'),
    (WEBSITE_SCOPE, 'Website')
]


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    display_name = fields.Char(string='Full name', compute='_get_display_name', store=True)
    magento_binding_ids = fields.One2many('magento.product.attribute', 'openerp_id', string='Magento bindings')
    type = fields.Selection(PRODUCT_ATTRIBUTE_TYPES, string='Type', required=True, default='select')
    display_type = fields.Selection(PRODUCT_ATTRIBUTE_TYPES, string='Type', required=True, default='select')
    default_value = fields.Char('Default value')
    scope = fields.Char(string='Scope')
    technical_name = fields.Char(string='Technical name')
    is_system = fields.Boolean('Is system?')
    manual_mapping = fields.Boolean('Manual mapping?', help="""If checked then it means it is mapped into some concrete
                                                               field on product and it won't be added into
                                                               'Additional data' of the product""", default=False)

    attribute_scope = fields.Selection(PRODUCT_ATTRIBUTE_SCOPES, string='Scope', default='global', required=True)
    should_export = fields.Boolean(string='Should export?', compute='_compute_should_export')
    is_required = fields.Boolean(string='Is required?', default=False)
    is_visible_on_front = fields.Boolean(default=False)
    is_global = fields.Boolean(default=False)

    @api.model
    def _get_name_search_domain(self):
        ctx = self.env.context
        is_manual_dom, res_dom = super(ProductAttribute, self)._get_name_search_domain()

        if is_manual_dom and not res_dom:
            return is_manual_dom, []

        if ctx.get('search_from_attr_type', False):
            is_manual_dom = True
            attr_types = ctx['search_from_attr_type']
            res_dom.append(('type', 'in', attr_types))

        return is_manual_dom, res_dom

    @api.depends('name', 'technical_name')
    def _get_display_name(self):
        for record in self:
            res = record.name
            if record.technical_name and res:
                res = res + ' (%s)' % (record.technical_name)
            record.display_name = res

    def remove_from_products(self):
        self.ensure_one()

        if self.env.user.id != SUPERUSER_ID:
            raise Warning(_('Only Administrator is allowed to remove attributes from all products!'))

        if not self.use_in_products:
            model_name = None

            if self.type in (SELECT_TYPE, CONFIGURABLE_TYPE):
                model_name = 'product.attributes.data'
            elif self.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE):
                model_name = 'product.textual.attributes.data'

            if model_name:
                attributes_data = self.env[model_name].search([('attr_id', '=', self.id)])
                if attributes_data:
                    attributes_data.unlink()

        return True

    @api.depends('is_system', 'manual_mapping')
    def _compute_use_in_products(self):
        for record in self:
            record.use_in_products = not (record.is_system or record.manual_mapping)

    @api.model
    def create(self, vals):
        if vals.get('type', None) == CONFIGURABLE_TYPE:
            vals['variant_attribute'] = True
        else:
            vals['variant_attribute'] = False

        res = super(ProductAttribute, self).create(vals)
        return res

    def write(self, vals):
        if 'type' in vals:
            if vals['type'] == CONFIGURABLE_TYPE:
                vals['variant_attribute'] = True
            else:
                vals['variant_attribute'] = False

        res = super(ProductAttribute, self).write(vals)
        return res

    def _compute_should_export(self):
        backends = self.env['magento.backend'].search([]).filtered(
            lambda rec: rec.product_attributes_sync_type == ATTRS_ODOO_MASTER)

        for attr in self:
            attr.should_export = len(backends) > 0

    def button_export_to_magento(self):
        self.ensure_one()
        return self.create_bindings()

    def remove_empty_bindings(self):
        self.ensure_one()
        empty_bindings = self.magento_binding_ids.filtered(lambda rec: not rec.magento_id.strip())
        return empty_bindings.unlink()

    def _prepare_specific_binding_vals(self, backend):
        self.ensure_one()
        return {
            'magento_code': self.technical_name,
            'is_configurable': self.type == CONFIGURABLE_TYPE,
            'magento_id': None
        }

    def _create_bindings_for_values(self, backend):
        self.ensure_one()
        for value in self.value_ids:
            backend.create_bindings_for_model(value, 'magento_binding_ids')
        return True

    def create_bindings(self):
        self.ensure_one()
        backends = self.env['magento.backend'].search([('product_attributes_sync_type', '=', ATTRS_ODOO_MASTER)])
        is_selection = self.type in (SELECT_TYPE, CONFIGURABLE_TYPE)

        for backend in backends:
            backend.create_bindings_for_model(self, 'magento_binding_ids')

            if is_selection:
                self._create_bindings_for_values(backend)

        return True

    @api.onchange('type')
    def onchange_attribute_type(self):
        if self.type == CONFIGURABLE_TYPE:
            self.attribute_scope = GLOBAL_SCOPE

        elif self.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE):
            self.value_ids = []

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    magento_binding_ids = fields.One2many('magento.product.attribute.value', 'openerp_id', 'Magento bindings')

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    active = fields.Boolean('Active', default=True)
    admin_name = fields.Char('Admin value')
    magento_binding_ids = fields.One2many('magento.product.attribute.value', 'openerp_id', 'Magento bindings')

    def _prepare_binding_for_backend(self, backend):
        self.ensure_one()

        res = {
            'openerp_id': self.id,
            'magento_id': None,
            'backend_id': backend.id,
        }

        return res

    def _create_binding_for_backend(self, backend):
        self.ensure_one()
        binding_data = self._prepare_binding_for_backend(backend)
        res = self.env['magento.product.attribute.value'].create(binding_data)
        return res

    _sql_constraints = [
        ('value_company_uniq', 'Check(1=1)', 'This attribute value already exists!'),
    ]


class MagentoProductAttribute(models.Model):
    _name = 'magento.product.attribute'
    _description = 'Magento Product Attribute'
    _inherit = 'magento.binding'
    _inherits = {'product.attribute': 'openerp_id'}

    openerp_id = fields.Many2one('product.attribute', 'Product attribute', required=True, ondelete='cascade')
    magento_code = fields.Char(string='Magento code')
    is_configurable = fields.Boolean('Is configurable', default=False)


    magento_attribute_value_ids = fields.One2many(
        comodel_name='magento.product.attribute.value',
        inverse_name='magento_attribute_id',
        string='Magento attribute bindings',
        readonly=True
    )

    @api.model
    def fields_to_update_on_magento(self):
        return ['name', 'type', 'magento_code', 'attribute_scope']

    _sql_constraints = [
        ('backend_oe_uniq', 'unique(backend_id, openerp_id)',
         'Odoo product attribute can be linked with only one product attribute per Magento backend!'),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if 'search_system_from_backend_id' in self.env.context:
            if not self.env.context['search_system_from_backend_id']:
                return False

            backend_id = int(self.env.context['search_system_from_backend_id'])
            args = [('backend_id', '=', backend_id), ('is_system', '=', True)]

        return super(MagentoProductAttribute, self).name_search(name, args, operator, limit)

    @job(default_channel='root.magento')
    @api.model
    def import_batch(self, backend, magento_attribute_set, filters=None):
        """ Prepare the import of records modified on Magento """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(magento_attribute_set, filters=filters)

    @job(default_channel='root.magento')
    @related_action(action='related_action_magento_link')
    @api.model
    def import_record(self, backend, magento_id, magento_attribute_set_ids, force=False):
        """ Import a Magento record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(magento_id, magento_attribute_set_ids, force=force)


class MagentoProductAttributeValue(models.Model):
    _name = 'magento.product.attribute.value'
    _description = 'Magento Product attribute value'
    _inherit = 'magento.binding'
    _inherits = {'product.attribute.value': 'openerp_id'}

    magento_attribute_id = fields.Many2one(
        'magento.product.attribute',
        compute='_compute_magento_attribute_id',
        store=True,
        string='Magento attribute binding'
    )

    openerp_id = fields.Many2one('product.attribute.value', 'Product attribute value', required=True,
                                 ondelete='cascade')

    @api.depends('openerp_id', 'openerp_id.attribute_id', 'openerp_id.attribute_id.magento_binding_ids')
    def _compute_magento_attribute_id(self):
        for record in self:
            res = False

            for binding in record.openerp_id.attribute_id.magento_binding_ids.filtered(
                    lambda rec: rec.backend_id.id == record.backend_id.id):
                res = binding.id
                break

            record.magento_attribute_id = res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if 'search_from_attr_id' in self.env.context and 'search_from_backend_id' in self.env.context:
            if not (self.env.context['search_from_attr_id'] and self.env.context['search_from_backend_id']):
                return False

            attr_id = int(self.env.context['search_from_attr_id'])
            backend_id = int(self.env.context['search_from_backend_id'])
            args = [('backend_id', '=', backend_id), ('magento_attribute_id', '=', attr_id)]

        return super(MagentoProductAttributeValue, self).name_search(name, args, operator, limit)

    _sql_constraints = [
        ('magento_uniq', 'unique(backend_id, openerp_id, magento_attribute_id)',
         'Odoo product attribute value can be linked with only one product attribute option per Magento backend!'),
    ]
