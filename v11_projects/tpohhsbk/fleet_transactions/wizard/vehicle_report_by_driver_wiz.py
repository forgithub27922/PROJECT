from odoo import models, fields, api

class VehilceReportByDriver(models.TransientModel):

    _name = 'vehicle.report.by.driver'

    driver_id = fields.Many2one('res.partner', 'Driver/Custodian')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Start Date')

    @api.multi
    def print_report(self):
        """
        This method will print the vehicle transaction report by Driver/Custodian.
        --------------------------------------------------------------------------
        @param self: object pointer
        """
        data = {}
        data['form'] = self.read([])
        return self.env.ref('fleet_transactions.report_vehicle_transaction_by_driver'). \
            report_action(self.ids, data=data)