# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _


class RejectRequestWizard(models.TransientModel):
    _name = 'reject.request.wizard'
    _description = 'Reject Vacation/Leave Request Wizard'

    reject_reason = fields.Text("Reject Reason")

    def action_confirm(self):
        """
        This method will reject the leave / vacation and update reject reason.
        It will also update the related tracking line
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        current_id = self.env.context.get('active_id')
        request = self.env['hr.leave'].sudo().browse(current_id)
        request.write({'rejection': self.reject_reason})
        request.action_refuse()
