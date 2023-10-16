from odoo import models, fields, _
import tempfile
import base64
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import objectify
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountMove(models.Model):
    _inherit = "account.move"

    xml_filename = fields.Char(
        string="Nombre XML",
    )
    xml_file = fields.Binary(
        string="XML", attachment=True
    )
    xml_import_id = fields.Many2one(
        comodel_name="xml.import.invoice",
        string="XML import",
        required=False,
    )

