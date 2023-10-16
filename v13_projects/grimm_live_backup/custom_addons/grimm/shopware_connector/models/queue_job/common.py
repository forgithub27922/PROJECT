# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models, tools, _


class QueueJob(models.Model):

    _inherit = 'queue.job'

    rec_id = fields.Char('Model Record ID', compute='_compute_rec_id',
                              readonly=True, store=True)

    @api.depends('func_string')
    def _compute_rec_id(self):
        for record in self:
            rec_list = record.record_ids
            if rec_list:
                record.rec_id = rec_list[0]
