from odoo import models, api


# PARSER

class CustomerReport(models.AbstractModel):
    _name = 'report.hotel_mangement_14.report_customer'
    _description = 'Customer Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids and data.get('ids', []):
            docids = data['ids']
        cust_obj = self.env['customer.customer']
        docs = cust_obj.browse(docids)
        print("\n\ndata['form']['room_id'][0]", data)
        return {
            'doc_ids': docids,
            'doc_model': 'customer.customer',
            'data': data,
            'docs': docs,
            'total_ser_charges': self.total_ser_charges,
            'total_taxes': self.total_taxes
        }

    def total_ser_charges(self, cust_charges):
        total_charges = 0.0
        print("--------------->", cust_charges)
        for charges in cust_charges:
            total_charges += charges.total_charges_service
        return total_charges

    def total_taxes(self, taxe):
        tax = 0.0
        for charges in taxe:
            tax += charges.taxes
        return tax
