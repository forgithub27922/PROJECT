# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class HrAllowances(models.TransientModel):

    _name = 'hr.allowances'
    _description = 'Allowances'
    _rec_name = 'allowance_id'

    allowance_id = fields.Many2one('hr.travel.allowance.head',
                                   string='Allowance Head', ondelete='cascade')
    done_by = fields.Selection([('company', 'Company'),
                                ('employee', 'Employee'),
                                ('not_applicable', 'Not Applicable')], string='Done by')
    travel_id = fields.Many2one('wiz.allowances',
                                string='Travel',
                                ondelete='cascade')


class WizAllowances(models.TransientModel):
    _name = 'wiz.allowances'

    travel_alw_ids = fields.One2many(
        'hr.allowances', 'travel_id', string='Travel Allowances')

    @api.multi
    def get_allowances(self):
        context = self._context
        alw_obj = self.env['hr.travel.allowance.configuration']
        travel_obj = self.env['hr.travel']
        active_rec = travel_obj.browse(context.get('active_id'))
        country_id = context.get('country_id')
        active_rec.allowance_ids.unlink()
        for rec in self:
            for travel in rec.travel_alw_ids:
                alw_record = alw_obj.search([
                    ('allowance_id', '=', travel.allowance_id.id),
                    ('done_by', '=', travel.done_by)])
                if not alw_record:
                    raise ValidationError(_('No Allowances Found'))
                for alw in alw_record:
                        vals = { 'name': alw.name,
                                 'allowance_head_id':alw.allowance_id.id,
                                 'done_by': alw.done_by,
                                 'based_on': alw.based_on,
                                 'amount': alw.amount,
                                 'currency_id': alw.currency_id.id,
                                }
                        if alw.based_on == 'country' and alw.country_id.id == country_id:
                            active_rec.write({'allowance_ids': [(0,0,vals)]})
                        if alw.based_on == 'country_group' and alw.country_group_id.country_ids:
                            if country_id in alw.country_group_id.country_ids.ids:
                                active_rec.write({'allowance_ids': [(0,0,vals)]})

