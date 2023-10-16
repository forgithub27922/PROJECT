from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'barcodes.barcode_events_mixin']

    barcode = fields.Char('Barcode', related='product_variant_ids.barcode', readonly=False, required=True)
    scanned_barcode = fields.Char('Barcode')

    _sql_constraints = [
        ('barcode_uniq', 'unique (barcode)', "A barcode can only be assigned to one product !"),
    ]

    def on_barcode_scanned(self, barcode):
        """
        Overridden barcode scanning method to update the scanning barcode field
        -----------------------------------------------------------------------
        @param self: object pointer
        @param barcode: The scanned barcode
        """
        self.scanned_barcode = barcode

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overridden create() method to check the barcode scanned!
        --------------------------------------------------------
        @param self: object pointer
        @param vals_list: List of dictionary containing fields and their values
        :return: Recordset
        """
        for data in vals_list:
            if data.get('scanned_barcode'):
                if data['scanned_barcode'] != data['barcode']:
                    raise UserError(_('The Barcode scanned does not match to the product barcode!'))
            else:
                raise UserError(_('Please scan the Barcode to create the product!!!'))
        return super(ProductTemplate, self).create(vals_list)

    def write(self, vals):
        """
        Overridden write() method to check the barcode scanned!
        -------------------------------------------------------
        @param self: object pointer
        @param vals: Dictionary containg fields and values
        :return: True
        """
        for product in self:
            barcode = vals.get('barcode') and vals['barcode'] or product.barcode
            if vals.get('scanned_barcode'):
                if vals['scanned_barcode'] != barcode:
                    raise UserError(_('Barcode as it does not match with product barcode.'))
            else:
                if product.scanned_barcode:
                    if product.scanned_barcode != barcode:
                        raise UserError(_('Barcode as it does not match with product barcode.'))
                else:
                    raise UserError(_('The Barcode scanned does not match to the product barcode!'))
            vals.update({'scanned_barcode': ''})
        return super(ProductTemplate, self).write(vals)