# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class WizRejectRequest(models.TransientModel):

    _name = 'wiz.reject.job.offer'

    reject_reason = fields.Text('Cancel Reason')


    def reject(self):
        """
        Set Reason of cancel in job offer.
        :return: True
        """
        act_id = self._context.get('active_id')
        act_mdl = self._context.get('active_model')
        if act_id and act_mdl:
            wiz_rec = self.env[act_mdl].browse(act_id)
            wiz_rec.write({'state': 'cancel', 'reason': self.reject_reason})
        return True
