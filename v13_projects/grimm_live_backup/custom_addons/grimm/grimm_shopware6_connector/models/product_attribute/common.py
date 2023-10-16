# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.tools.translate import _
from odoo.addons.component.core import Component

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    shopware6_position = fields.Integer(string="Shopware6 Position")