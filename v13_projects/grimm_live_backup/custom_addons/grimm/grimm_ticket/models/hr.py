# -*- coding: utf-8 -*-

from openerp import models, fields


class Department(models.Model):
    _inherit = 'hr.department'

    ticket_permission = fields.Selection(selection=[('public', 'Public'), ('private', 'Private')],
                                         string='Ticket Permission', default='public', copy=True,
                                         track_visibility="always", required=True,
                                         help='Permission for Ticket System'
                                              'Public: all employees can see the tickets'
                                              'Private: only employees of this department can see the tickets')
