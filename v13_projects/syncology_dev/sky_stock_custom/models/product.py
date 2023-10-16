from odoo import fields, models, api, _


class Product(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'barcodes.barcode_events_mixin']

    barcode = fields.Char('Barcode', copy=False,
                          help="International Article Number used for product identification.")
    _sql_constraints = [
        ('barcode_uniq', 'unique (barcode)', "A barcode can only be assigned to one product !"),
    ]

    def on_barcode_scanned(self, barcode):
        """
        Overridden barcode scanning method to update the barcode field
        ---------------------------------------_-----------------------
        @param self: object pointer
        @param barcode: The scanned barcode
        """
        for product in self:
            product.barcode = barcode
