# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    default_block = fields.Many2one(
        comodel_name='sale.block.reason',
        string='Block Reason',
        help="Set a reason to block this customers sales orders.")

    @api.model
    def _commercial_fields(self):
        commercial_fields = super(ResPartner, self)._commercial_fields()
        commercial_fields.append('default_block')
        return commercial_fields
