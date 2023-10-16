# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    equip_amount = fields.Float(string='Amount')
    equip_state = fields.Selection(selection=[
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo')
    ], string="Equip Status", default="Activo")
    account_analytic_id = fields.Many2one('account.analytic.account', store=True, string='Analytic Account', compute='_compute_analytic_id_and_tag_ids', readonly=False)

    @api.depends('name', 'account_analytic_id')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            rec.account_analytic_id = self.env.user.account_analytic_id

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    account_analytic_id = fields.Many2one('account.analytic.account', store=True, string='Analytic Account', compute='_compute_analytic_id_and_tag_ids', readonly=False)

    @api.depends('name', 'account_analytic_id')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            rec.account_analytic_id = self.env.user.account_analytic_id
