from odoo import models, fields, api


class VehicleReportByDriver(models.AbstractModel):
    _name = 'report.fleet_transactions.vehicle_report_by_driver'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        # Fetch data from wizard
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        # Report Details
        fleet_txn_obj = self.env['fleet.transaction']
        domain = [
            '|', ('to_partner_id', '=', data['form'][0]['driver_id'][0]),
            ('from_partner_id', '=', data['form'][0]['driver_id'][0]),
        ]
        if data['form'][0]['start_date']:
            domain.append(('date', '>=', data['form'][0]['start_date']))
        if data['form'][0]['end_date']:
            domain.append(('date', '<=', data['form'][0]['end_date']))
        txn_type = {
            'location': 'Location',
            'personal': 'Driver/Custodian',
            'sell': 'Sell',
            'scrap': 'Scrap',
            'gift': 'Gift'
        }
        txns = fleet_txn_obj.search(domain)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'driver': data['form'][0]['driver_id'][1],
            'st_dt': data['form'][0]['start_date'],
            'en_dt': data['form'][0]['end_date'],
            'txns': txns,
            'txn_type':txn_type
        }
