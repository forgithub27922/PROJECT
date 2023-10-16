# -*- coding: utf-8 -*-
# Copyright 2019. Grimm-Gastronomibedarf.de
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pytz
from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from ...components.backend_adapter import SHOPWARE_DATETIME_FORMAT
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

class PropertySet(models.Model):
    _name = 'property.set'
    _description = 'Property Set'

    name = fields.Char('Name', required=True)
    position = fields.Integer('Position')
    comparable = fields.Boolean('Comparable')
    sort_mode = fields.Integer('Sort Mode')
    product_attribute_ids = fields.Many2many(comodel_name='product.attribute',
                                             relation='property_set_product_attr_rel', column1='property_set_id',
                                             column2='attr_id')

