# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductWarrantyType(models.Model):
    _name = "product.warranty.type"
    _description = "Type for Warranty"

    name = fields.Char("Warranty Type", required=True)
