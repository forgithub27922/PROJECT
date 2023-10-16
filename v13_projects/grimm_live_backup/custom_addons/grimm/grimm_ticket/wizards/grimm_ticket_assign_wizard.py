# -*- coding: utf-8 -*-
from openerp import api, fields, models


class GrimmTicketAssignWizard(models.TransientModel):
    _name = 'grimm.ticket.assign.wizard'
    _description = 'Grimm Ticket Assignment Wizard'

    ticket = fields.Many2one('grimm.ticket', 'Ticket', required=True)
    arranger = fields.Many2one(comodel_name="res.users", string="Arranger")
    department = fields.Many2one(comodel_name="hr.department", string="Department")

    def assign_ticket(self):
        res = False
        for wizard in self:
            if wizard.arranger:
                wizard.ticket.arranger = wizard.arranger
            if wizard.department:
                wizard.ticket.department = wizard.department

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'grimm.ticket',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
