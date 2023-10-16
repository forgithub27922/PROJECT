from odoo import models, api


class EmployeeReport(models.AbstractModel):
    _name = 'report.sky_hr_custom.report_employee'
    _description = 'Employee Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        The method used to return the data to be used on report
        ------------------------------------------------------------------------------------------------------
        :param docids: Ids of the records for which the report will be printed.
        :param data: A dictionary containing data such as context and if called from wizard the data of wizard
        :return: A dictionary containing values which can be used on the template of the report.
        """
        emp_obj = self.env['hr.employee']
        docs = emp_obj.browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'data': data,
            'docs': docs,
        }
