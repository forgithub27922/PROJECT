# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class WizRejectRequest(models.TransientModel):

    _name = 'wiz.reject.request'

    reject_reason = fields.Text('Retained Reason')

    @api.multi
    def reject(self):
        """
        Set details of rejecter employee's like Rejection Date, Rejection By
        and Reason of rejection.
        :return: True
        """
        for wiz in self:
            state = 'retained'
            if self.env.context.get('state', False) == 'reject':
                state = 'reject'
            act_id = self._context.get('active_id')
            act_mdl = self._context.get('active_model')
            request_obj = self.env[act_mdl]
            request = request_obj.browse(act_id)
            usr = self.env['res.users'].browse(self._uid)
            curr_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            comments = '\n' + 'Retain Date : ' + curr_date + '\n' + \
                'Retained By : ' + usr.name
            if wiz.reject_reason:
                comments += '\n' + 'Reason: ' + wiz.reject_reason or ' '
            if request.comments:
                comments += request.comments
            request.write({'state': state, 'comments': comments})
        return True
