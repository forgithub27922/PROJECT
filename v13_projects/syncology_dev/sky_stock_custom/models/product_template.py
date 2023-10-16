from odoo import fields, models, api, _


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
        for product in self:
            product.barcode = barcode