from odoo import fields, models, api, _


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        if self.pick_ids.contact_type == 'employee':
            for move_id in self.pick_ids.move_ids_without_package:
                self.env['stock.equipment'].create(
                    {
                        'unit': move_id.product_id.id,
                        'quantity': move_id.quantity_done,
                        'employee_id': self.pick_ids.employee_id.id,
                        'date': self.pick_ids.scheduled_date.date(),
                        'status': self.pick_ids.status_id.id,
                    }
                )
        return res
