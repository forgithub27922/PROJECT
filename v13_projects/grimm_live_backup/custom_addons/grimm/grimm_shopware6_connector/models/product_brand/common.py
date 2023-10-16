# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

class Shopware6GrimmProductBrand(models.Model):
    """ Binding Model for the Odoo Res Partner """
    _name = 'shopware6.grimm.product.brand'
    _inherit = 'shopware6.binding'
    _inherits = {'grimm.product.brand': 'openerp_id'}
    _description = 'Shopware6 Manufacturer'

    openerp_id = fields.Many2one(comodel_name='grimm.product.brand',
                              string='Grimm Product Brand',
                              required=True,
                              ondelete='cascade')

    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Partner to Target Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

class GrimmProductBrand(models.Model):
    """ Adds the ``one2many`` relation to the Magento bindings
    (``magento_bind_ids``)
    """
    _inherit = 'grimm.product.brand'

    shopware6_brand_ids = fields.One2many(
        comodel_name='shopware6.grimm.product.brand',
        inverse_name='openerp_id',
        string='Shopware6 Manufacturer Bindings',
    )
    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_brand_ids')
        return True

class Shopware6BrandAdapter(Component):
    _name = 'shopware6.grimm.product.brand.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.grimm.product.brand'

    _shopware_uri = 'api/v3/product-manufacturer/'

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('GET', '%s%s' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update category on the Shopware system """
        return self._call('PATCH', '%s%s' % (self._shopware_uri, id), data)

    def create(self, data):
        return self._call('POST', self._shopware_uri, data)




class GrimmProductBrandListener(Component):
    _name = 'grimm.product.brand.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['grimm.product.brand']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware6_brand_ids:
            shopware_bind.with_delay().export_record(fields=fields)

class Shopware6GrimmProductBrandListener(Component):
    _name = 'shopware6.grimm.product.brand.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.grimm.product.brand']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()