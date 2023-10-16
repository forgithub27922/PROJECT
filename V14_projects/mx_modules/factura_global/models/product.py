# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

class product_template(models.Model):
    _inherit = "product.template"

    f_global=fields.Boolean(string='Se usa en  Factura Global', default=False)
    cuenta_tasa_0=fields.Many2one('account.account', string="Cuenta de ventas a tasa 0",company_dependent=True)
    cuenta_tasa_16=fields.Many2one('account.account', string="Cuenta de ventas a tasa 16", company_dependent=True)

