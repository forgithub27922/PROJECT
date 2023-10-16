# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools.mail import append_content_to_html


class FeePaymentWizard(models.TransientModel):

    _name = 'fee.collection.dues.wizard'
    _description = 'fee.collection.dues.wizard'
    
    date_from = fields.Date('Date from', required=True)
    date_to = fields.Date('Date to', default=datetime.today(), required=True)
    filter_status = fields.Selection([('all','All'),('refunded', 'Refunded'),('unpaid','Unpaid'),('paid','Paid')],'Filter By',default='all')
    student_id = fields.Many2many('academic.student', string="Students", domain="[('state','!=','draft')]")
    
    
    def check_report(self):
        data = {}
        data['form'] = self.read([ 'date_from', 'date_to', 'filter_status','student_id'])[0]
        
        return self.env.ref('sms_core.fee_collection_dues_report').report_action(self, data=data, config=False)
        
    
#     def student_fee_payment(self):
#         inst_id = self.env.context.get('installment_id', False)
#         rec = self.env['fee.policy.line'].browse(inst_id)
#         print("RRRRRRR;;;;;;--> ",self.student_fee_ids)
#         
#         
#         call = self.env['student.fee'].pay_student_fee_cm([self.student_fee_ids])