##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api, _


class ProductBarcode(models.TransientModel):
    _name = 'product.barcode.wizard'
    _inherit = 'barcodes.barcode_events_mixin'
    _description = 'Product Barcode Wizard'

    model = fields.Char('Model', required=True, readonly=True)
    res_id = fields.Integer('Res')
    method = fields.Char('Method', required=True, readonly=True)
    state = fields.Selection([('waiting', 'Waiting'), ('warning', 'Warning')], 'State', default='waiting', readonly=True)
    status = fields.Text('Status', readonly=True, default='Scan a Barcode')
