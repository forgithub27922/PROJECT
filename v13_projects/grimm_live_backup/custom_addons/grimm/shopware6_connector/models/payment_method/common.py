# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.addons.component.core import Component
import logging
from datetime import datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30


class Shopware6PaymentMode(models.Model):
    _name = 'shopware6.account.payment.mode'
    _inherit = 'shopware6.binding'
    _description = 'Shopware Payment Method'
    _parent_name = 'backend_id'


    name = fields.Char("Name", required=True, readonly=True)
    position = fields.Char("Position", required=True, readonly=True)
    description = fields.Char("Position", required=True, readonly=True)
    shopware6_active = fields.Boolean(readonly=True)
    odoo_payment_mode_id = fields.Many2one(comodel_name='account.payment.mode', string='Odoo Payment Mode')


class Shopware6PaymentMode(Component):
    _name = 'shopware6.account.payment.mode.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.account.payment.mode'

    _shopware_uri = 'api/v3/payment-method/'

