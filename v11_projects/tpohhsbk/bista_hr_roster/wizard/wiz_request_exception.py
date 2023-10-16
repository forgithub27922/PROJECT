# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizRejectRequestException(models.TransientModel):

    _name = 'wiz.reject.request.exception'

    reject_reason = fields.Text('Reject Reason')

    @api.multi
    def reject(self):
        if self._context.get('overtime'):
            act_id = self._context.get('active_id')
            act_mdl = self._context.get('active_model')
            req_obj = self.env[act_mdl]
            req_overtime = req_obj.browse(act_id)

            req_overtime.write(
                {'state': 'reject', 'rejection_reason': self.reject_reason})
            return True

        act_id = self._context.get('active_id')
        act_mdl = self._context.get('active_model')
        req_obj = self.env[act_mdl]
        req_exception = req_obj.browse(act_id)
        usr = self.env['res.users'].browse(self._uid)

        comments = '\n' + \
            'Rejected By : ' + usr.name
        if self.reject_reason:
            comments += '\n' + 'Reason: ' + self.reject_reason or ' '
        if req_exception.comments:
            comments += req_exception.comments
        req_exception.write({'state': 'reject', 'comments': comments})


class WizCancel(models.TransientModel):

    _name = 'wiz.cancel'

    cancel_reason = fields.Text('Cancel Reason')

    @api.multi
    def reject(self):
        act_id = self._context.get('active_id')
        act_mdl = self._context.get('active_model')
        req_obj = self.env[act_mdl]
        req_overtime = req_obj.browse(act_id)

        req_overtime.write(
            {'state': 'cancel', 'cancel_reason': self.cancel_reason})
        return True
