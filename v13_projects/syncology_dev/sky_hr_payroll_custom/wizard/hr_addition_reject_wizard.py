# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _


class HrAdditionRejectWizard(models.TransientModel):
    _name = 'hr.addition.reject.wizard'
    _description = 'Hr Addition Reject Wizard'

    reject_reason = fields.Text("Reject Reason")

    def action_confirm(self):
        """
        This method will write reject reason in hr addition reject field and update state to reject
        -------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        current_id = self.env.context.get('active_id')
        addition = self.env['hr.addition'].browse(current_id)
        addition.write({'rejection_reason': self.reject_reason, 'state': 'rejected'})
