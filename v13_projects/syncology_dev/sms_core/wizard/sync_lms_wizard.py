 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class SyncLmsWizard(models.TransientModel):
 
    _name = "sync.lms.wizard"
    _description = "Sync Lms wizard"
    
    reason = fields.Selection([('Fee_defaulter','Fee Defaulter'),('other','Other')],'Reason',default='Fee_defaulter')
    
    def btn_active_deactive_lms(self):
        """
        This method is called by user to activate or deactivate student on lms.
        """
        flg = self.env.context.get('lms_action')
        s_id =  self.env.context.get('active_std')
        std_id = self.env['academic.student'].browse(s_id)
        print("this is student id",std_id)
        res = self.env['academic.student'].active_inactive_student(std_id,self.reason,flg)
        return res

