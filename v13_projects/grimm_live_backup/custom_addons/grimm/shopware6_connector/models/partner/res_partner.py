# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.addons.component.core import Component
import logging
import xmlrpc.client
from odoo import api, models, fields
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.connector.exception import IDMissingInBackend

_logger = logging.getLogger(__name__)

class Shopware6ResPartnerBatchImporter(Component):
    """ Import the Shopware Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware6.res.partner.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.res.partner']

    '''
    def _import_record(self, shopware6_id, job_options=None, **kwargs):
        """ Delay a job for the import """
        return super(ShopwareResPartnerBatchImporter, self)._import_record(
            shopware6_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        updated_ids = self.backend_adapter.search(filters)
        for record_id in updated_ids:
            self._import_record(record_id.get('id'))
    '''

class Shopware6ResPartner(models.Model):
    """ Binding Model for the Odoo Res Partner """
    _name = 'shopware6.res.partner'
    _inherit = 'shopware6.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Target Shopware6 Partner'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                              string='Partner',
                              required=True,
                              ondelete='cascade')

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(shopware6_id, force=force)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Partner to Target Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class ResPartner(models.Model):
    """ Adds the ``one2many`` relation to the Shopware bindings
    (``shopware6_bind_ids``)
    """
    _inherit = 'res.partner'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.res.partner',
        inverse_name='openerp_id',
        string='Shopware Bindings',
    )

    shopware6_address_ids = fields.One2many(
        comodel_name='shopware6.address',
        inverse_name='openerp_id',
        string='Shopware6 Address Bindings',
    )
    '''
    shopware_invoice_address_ids = fields.One2many(
        comodel_name='shopware.invoice.address',
        inverse_name='openerp_id',
        string='Shopware Invoice Address Bindings',
    )
    '''

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True


class Shopware6Address(models.Model):
    _name = 'shopware6.address'
    _inherit = 'shopware6.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Shopware6 Address'

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner',
                                 required=True,
                                 ondelete='cascade')
    is_default_billing = fields.Boolean(string='Default Invoice')
    is_default_shipping = fields.Boolean(string='Default Shipping')
    '''
    shopware_partner_id = fields.Many2one(comodel_name='shopware6.res.partner',
                                         string='Shopware Partner',
                                         ondelete='cascade')
    backend_id = fields.Many2one(
        related='shopware_partner_id.backend_id',
        comodel_name='shopware6.backend',
        string='Shopware Backend',
        store=True,
        readonly=True,
        # override 'shopware6.binding', can't be INSERTed if True:
        required=False,
    )
    
    shop_id = fields.Many2one(
        #related='shopware6_partner_id.shop_id',
        comodel_name='shopware6.shop',
        string='Shopware6 Shop',
        store=True,
        readonly=True,
    )
    is_shopware_order_address = fields.Boolean(
        string='Address from a Shopware Order',
    )

    _sql_constraints = [
        ('openerp_uniq', 'unique(backend_id, openerp_id)',
         'A partner address can only have one binding by backend.'),
    ]
    '''
'''
class Shopware6InvoiceAddress(models.Model):
    _name = 'shopware.invoice.address'
    _inherit = 'shopware6.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Shopware6 Address'

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner',
                                 required=True,
                                 ondelete='cascade')
    is_default_billing = fields.Boolean(string='Default Invoice')
    is_default_shipping = fields.Boolean(string='Default Shipping')
    shopware_partner_id = fields.Many2one(comodel_name='shopware.res.partner',
                                         string='Shopware Partner',
                                         required=True,
                                         ondelete='cascade')
    backend_id = fields.Many2one(
        related='shopware_partner_id.backend_id',
        comodel_name='shopware6.backend',
        string='Shopware Backend',
        store=True,
        readonly=True,
        # override 'shopware6.binding', can't be INSERTed if True:
        required=False,
    )
    shop_id = fields.Many2one(
        #related='shopware6_partner_id.shop_id',
        comodel_name='shopware6.shop',
        string='Shopware6 Shop',
        store=True,
        readonly=True,
    )
    is_shopware_order_address = fields.Boolean(
        string='Address from a Shopware Order',
    )

    _sql_constraints = [
        ('openerp_uniq', 'unique(backend_id, openerp_id)',
         'A partner address can only have one binding by backend.'),
    ]
'''
class ResPartnertAdapterShopware6(Component):
    _name = 'shopware6.res.partner.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.res.partner'

    _shopware_uri = 'api/v3/customer/'

    def _call(self, method, api_call, arguments=None):
        try:
            return super(ResPartnertAdapterShopware6, self)._call(method, api_call, arguments)
        except xmlrpc.client.Fault as err:
            # this is the error in the Shopware API
            # when the product does not exist
            if err.faultCode == 101:
                raise IDMissingInBackend
            else:
                raise

    def write(self, id, data):
        """ Update records on the external system """
        # XXX actually only ol_catalog_product.update works
        # the PHP connector maybe breaks the catalog_product.update
        return self._call('PATCH', self._shopware_uri + id, data)

    def create(self,data):
        """ Create Partner records on the external system """
        return self._call('POST','%s' % self._shopware_uri,data)

    def delete(self,id):
        """ Delete partner records on the external system """
        return self._call('DELETE', self._shopware_uri + id, {})

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        result = self._call('GET','%s' % self._shopware_uri,[filters] if filters else [{}])
        return result.get('data', result)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        result =  self._call('GET', '%s%s' % (self._shopware_uri,id), [{}])
        return result.get('data', result)

    def get_child_address(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        result = self._call('GET', '%s%s/addresses' % (self._shopware_uri,id), [{}])
        return result.get('data', result)


class Shopware6AddressAdapter(Component):
    _name = 'shopware6.address.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.address'

    _shopware_uri = 'api/v3/order-address/'

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        result =  self._call('GET', '%s%s' % (self._shopware_uri,id), [{}])
        return result.get('data', result)

    def get_country(self, id):
        result = self._call('get', 'api/v3/country/%s' % (id), [{}])
        return result.get('data', result)

########################################################################################################################

'''
class ShopwareSupplier(models.Model):
    """ Binding Model for the Odoo Res Partner """
    _name = 'shopware.supplier'
    _inherit = 'shopware6.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Shopware Supplier'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                              string='Partner',
                              required=True,
                              ondelete='cascade')

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Partner to Target Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class ResPartner(models.Model):
    """ Adds the ``one2many`` relation to the Shopware bindings
    (``shopware_bind_ids``)
    """
    _inherit = 'res.partner'

    shopware_supplier_ids = fields.One2many(
        comodel_name='shopware.supplier',
        inverse_name='openerp_id',
        string='Shopware Supplier Bindings',
    )
    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_supplier_ids')
        return True

class SupplierAdapter(Component):
    _name = 'shopware6.supplier.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.supplier'

    _shopware_uri = 'manufacturers/'

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update category on the Shopware system """
        return self._call('put', '%s%s' % (self._shopware_uri, id), data)

    def create(self, data):
        return self._call('post', self._shopware_uri, data)
'''
