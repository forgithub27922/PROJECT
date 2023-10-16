from odoo import models, fields, api


class CustomerReport(models.AbstractModel):
    # Inheriting the Report Parser
    _inherit = 'report.hotel_mangement_14.report_customer'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Calling the method of the parent parser
        res = super()._get_report_values(docids, data=data)
        # Updating new variables and methods

        res.update({

            'my_method': self.my_method
        })
        return res

    @api.model
    def my_method(self):
        return "my METHOD"
