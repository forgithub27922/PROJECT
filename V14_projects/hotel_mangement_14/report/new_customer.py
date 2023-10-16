from odoo import models, api


# PARSER

class CustomerReport(models.AbstractModel):
    _name = 'report.hotel_mangement_14.new_report_customer'
    _description = 'Customer Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids and data.get('ids', []):
            docids = data['ids']
        cust_obj = self.env['customer.customer']
        docs = cust_obj.browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'customer.customer',
            'data': data,

            'docs': docs,
            'new_method1': self.new_method1,
            'new_method2': self.new_method2,

        }
    def new_method1(self):
        return "My New Method One Called"

    def new_method2(self):
        return "My New Method Second Called"

