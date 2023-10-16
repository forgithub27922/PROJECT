# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from openerp.exceptions import ValidationError
import ast


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_email_logo = fields.Binary(string='Company Email Logo')
    product_desc_validation = fields.Boolean(string="Apply Validation?",default=False)
    valid_tags = fields.Char(string="Valid Tags", help="Remove other tags from product description.", default='[]')
    remove_attrs = fields.Char(string="Remove Attributes", help="Remove attributes from html tag.", default='[]')
    company_iban = fields.Char(string="IBAN")
    company_bank_name = fields.Char(string="Institute Name")

    @api.onchange('valid_tags','remove_attrs')
    def onchange_tags_attributes(self):
        try:
            valid_tags = ast.literal_eval(self.valid_tags)
            remove_attrs = ast.literal_eval(self.remove_attrs)
        except Exception as e:
            raise ValidationError(_('Wrong formating for Valid tags or remove attributes %s'%str(e)))

