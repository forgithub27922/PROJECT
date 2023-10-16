from odoo import models, fields, api

class VehilceReportByPeriod(models.TransientModel):

    _name = 'vehicle.report.by.period'

    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Start Date')

    @api.multi
    def print_report(self):
        """
        This method will print the vehicle transaction report by Period.
        ----------------------------------------------------------------
        @param self: object pointer
        """
        data = {}
        data['form'] = self.read([])
        return self.env.ref('fleet_transactions.report_vehicle_transaction_by_period'). \
            report_action(self.ids, data=data)