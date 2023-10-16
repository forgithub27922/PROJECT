# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

'''
To create document.
documentTypeId
orderId
documentMediaFileId
sent
config : documentNumber, documentComment



'''

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.addons.component.core import Component
import logging
import base64
from slugify import slugify
from datetime import datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action


IMPORT_DELTA_BUFFER = 30

class Shopware6Document(models.Model):
    _name = 'shopware6.document'
    _inherit = ['shopware6.binding']
    _description = 'Shopware6 Document'
    _parent_name = 'backend_id'

    name = fields.Char("Name")
    doc_number = fields.Char("Document Number")
    doc_comment = fields.Char("Document Comment")
    doc_datetime = fields.Datetime("Document Date")
    doc_type = fields.Char("Document Type")
    order_id = fields.Char("Order ID (Shopware6)")
    document = fields.Binary('Document File', attachment=True)

class Shopware6DocumentAdapter(Component):
    _name = 'shopware6.document.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.document'

    _shopware_uri = 'api/v3/document/'

    def create(self, data):
        self._shopware_uri = "api/_action/order/%s/document/%s"%(data.get("shopware6_id"),data.get("doc_type"))
        return self._call('POST', self._shopware_uri, data)

    def upload_file(self, binding):
        """ Update records on the external system """
        file_name = slugify(str(binding.name)+str(datetime.now()))
        file_data = base64.b64decode(binding.document)
        shopware_uri = "api/_action/document/%s/upload?fileName=%s&extension=pdf" % (binding.shopware6_id, file_name)
        return self._call('POST', shopware_uri, file_data)

class Shopware6DocumentListener(Component):
    _name = 'shopware6.document.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.document']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class Shopware6DocumentType(models.Model):
    _name = 'shopware6.document.type'
    _inherit = ['shopware6.binding']
    _description = 'Shopware6 Document Type'
    _parent_name = 'backend_id'


    name = fields.Char("Name", required=True)
    technical_name = fields.Char("Technical Name")
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')
    odoo_type_id = fields.Selection(string='Odoo Type', selection=[('credit', 'Credit Note'), ('delivery', 'Delivery Note'), ('invoice', 'Invoice'), ('invoice_cancel', 'Invoice Cancel')])

    def _get_is_shopware6_exported(self):
        self.is_shopware6_exported = False
        for this in self:
            this.is_shopware6_exported = True if this.shopware6_id else False

    def export_to_shopware6(self):
        for record in self:
            record.export_record()
        return True

class Shopware6DocumentTypeAdapter(Component):
    _name = 'shopware6.document.type.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.document.type'

    _shopware_uri = 'api/v3/document-type/'

    def _call(self, method, api_call, arguments=None):
        return super(Shopware6DocumentTypeAdapter, self)._call(method, api_call, arguments)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('get','%s' % self._shopware_uri,[filters] if filters else [{}])

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('get', '%s%s' % (self._shopware_uri,id), [{}])

class GrimmShopware6DocumentTypeListener(Component):
    _name = 'shopware6.document.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.document.type']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'updated_at' not in fields:
            record.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        if record.shopware6_id:
            record.with_delay().export_delete_record(record.backend_id, record.shopware6_id)

