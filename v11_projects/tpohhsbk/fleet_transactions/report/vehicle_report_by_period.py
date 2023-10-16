from odoo import models,fields,api

class VehicleReportByPeriod(models.AbstractModel):

    _name='report.fleet_transactions.vehicle_report_by_period'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        #Fetch data from wizard
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        #Report Details
        fleet_txn_obj = self.env['fleet.transaction']
        fleet_loc_obj = self.env['fleet.location']
        locations = fleet_loc_obj.search([])
        loc_dict = {}
        for loc in locations:

            domain = [
                '|', ('to_loc_id', '=', loc.id),
                ('from_loc_id', '=', loc.id),
                ('date', '>=', data['form'][0]['start_date']),
                ('date', '<=', data['form'][0]['end_date'])
            ]
            txns = fleet_txn_obj.search(domain)
            if txns.ids:
                loc_dict[loc.id] = {
                    'location': loc.name,
                    'txns': txns
                }
        txn_type = {
            'location': 'Location',
            'personal': 'Driver/Custodian',
            'sell': 'Sell',
            'scrap': 'Scrap',
            'gift': 'Gift'
        }
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'st_dt': data['form'][0]['start_date'],
            'en_dt': data['form'][0]['end_date'],
            'txn_type': txn_type,
            'locs': loc_dict
        }
