# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    partner_id = fields.Many2one('res.partner', 'Partner',
                                 help='For gratuity employee.')

    @api.model
    def create(self, vals):
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals.get('user_id'))
            vals.update({'partner_id': user.partner_id.id})
        else:
            partner_obj = self.env['res.partner']
            partner_vals = {'name': vals.get('name'),
                            'ref': vals.get('emp_id') or '',
                            'customer': False,
                            'supplier': False,
                            }
            partner_record = partner_obj.create(partner_vals)
            vals.update({'partner_id': partner_record.id,
                         'address_home_id': partner_record.id or False})
        return super(HrEmployee, self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            partner_rec, user = False, False
            if vals.get('user_id'):
                user = self.env['res.users'].browse(vals.get('user_id'))
            if rec.partner_id:
                partner_rec = rec.partner_id
                if not partner_rec:
                    partner_rec = user.partner_id
            if user and partner_rec:
                user.write({'partner_id': rec.partner_id.id,
                            'address_home_id': rec.partner_id.id or False})
            if not rec.partner_id and user:
                vals.update({'partner_id': user.partner_id.id,
                             'address_home_id': rec.partner_id.id or False})
        return super(HrEmployee, self).write(vals)
