# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
import base64
from odoo import api, fields, models, _


class wiz_employee_dos(models.TransientModel):
    _name = 'wiz.employee.docs'

    job_doc_id = fields.Many2one('hr.job.document', string="Document")

    @api.multi
    def btn_employee_docs(self):
        hr_doc_obj = self.env['hr.document']
        emp_id = self._context.get('active_id')
        if self._context.get('active_model') == 'hr.employee':
            employee_rec = self.env[self._context.get('active_model')].browse(
                emp_id)
        if self.job_doc_id:
            self.job_doc_id.employee_id = emp_id
            self.job_doc_id.applicant_id = False
            report_id = self.env.ref('hr_document.report_offer_letter')
            pdf_bin, _ = report_id.render_qweb_pdf(self.job_doc_id.id)
            vals = {
                'name': self.job_doc_id.name,
                'date_start': employee_rec.date_joining,
                'status': 'ongoing',
                'date_expiry': '',
                'employee_id': emp_id,
                'file': base64.b64encode(pdf_bin),
            }
            if vals:
                hr_doc_obj.create(vals)
        return self.env.ref(
            'hr_document.report_offer_letter').report_action(self.job_doc_id)
