# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client

from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in range(0, len(items), length):
        yield items[index:index + length]

class OdooProductImage(models.Model):
    _inherit = 'odoo.product.image'
    _order = 'position'

    record_inserted = fields.Selection([('server', 'Image Server'), ('manually', 'Manually'), ('magento', 'Magento Tabs')], string='Created From', default='manually')
    magento_image_id = fields.Many2one('product.image', string='Magento Image')
    magento_image = fields.Binary(string='Image', related='magento_image_id.manual_image_data')

    def unlink(self):

        if not self._context.get("allow"):
            for rec in self:
                if rec.record_inserted in ['server','magento']:
                    raise UserError(
                        _(u"You can not delete shopware image linked to Image server or Magento images. "
                          u"\nPlease delete it from source."))
        res = super(OdooProductImage, self).unlink()

        return res