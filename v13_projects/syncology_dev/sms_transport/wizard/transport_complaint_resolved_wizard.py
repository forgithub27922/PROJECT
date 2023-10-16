from odoo import api, fields, models, _

class TransportComplaintResolvedWizard(models.TransientModel):
    _name = "transport.complaint.resolve.wizard"
    _description = "Transport Complaint Resolve Wizard"

    resolve = fields.Text('Resolve')

    def action_resolve(self):
        self._context.get('active_id')
        res = self.env['transport.complaint.management'].browse(self._context.get('active_id')).write(
            {
                'resolve': self.resolve,
                'state': 'resolved'
            }
        )
        return res



