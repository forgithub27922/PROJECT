from odoo import models, api


class StudentFeeReport(models.AbstractModel):
    _name = 'report.sms_core.report_student_fee'
    _description = 'Student Fee Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        The method used to return the data to be used on report
        ----------------------------
        @param docids: Ids of the records for which the report will be printed.
        @param data: A dictionary containing data such as context and if called from wizard the data of wizard
        @return: A dictionary containing values which can be used on the template of the report.
        """
        if not docids and data.get('ids', []):
            docids = data['ids']
        stud_fee_obj = self.env['student.fee']
        docs = stud_fee_obj.browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'student.fee',
            'docs': docs,
        }