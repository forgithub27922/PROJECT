# -*- coding: utf-8 -*-
from odoo import fields, models, api


class WeekoffDay(models.Model):

    _name = 'weekoff.day'
    _description = 'Week Days'

    name = fields.Char(string='Name', translate=True)
    code = fields.Char(string='Code')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """add domain to prevent repeted week days"""
        week_off_ids = []
        args = args or []
        domain = []
        if self._context.get('add_domain'):
            active_id = self._context.get('roster_id')
            if active_id:
                week_off_ids = self.env['hr.roster'].\
                    browse(active_id).weekoff.ids
            domain = [('id', 'not in', week_off_ids)]
            self.search(domain + args, limit=limit)
        return super(
            WeekoffDay,
            self).name_search(
            name,
            args +
            domain,
            operator=operator,
            limit=limit)
