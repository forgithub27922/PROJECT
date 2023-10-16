# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models


class DailyPerformance(models.AbstractModel):
    _name = 'report.bista_hr_roster.report_daily_performance'

    def get_vals(self, objs, plan_out, act_out):
        return '{0:02.0f}:{1:02.0f}'.format(*divmod((plan_out - act_out) * 60, 60))




    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['roster.vs.attendance'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'roster.vs.attendance',
            'data': data,
            'docs': docs,
            'get_vals': self.get_vals,
        }
