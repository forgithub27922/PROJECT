# -*- coding: utf-8 -*-
# Copyright 2004-today Odoo SA (<http://www.odoo.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class WebShortcut(models.Model):
    _name = 'web.shortcut'
    _description = 'Adds a shortcut menu on the navigation.'

    name = fields.Char('Shortcut Name', size=64)
    action_id = fields.Many2one('ir.actions.act_window', ondelete='cascade')
    user_id = fields.Many2one('res.users', 'User Ref.', required=True,
                              ondelete='cascade', index=True,
                              default=lambda self: self.env.user)
    link = fields.Char('Link', required=True)

    _sql_constraints = [
        ('shortcut_unique', 'unique(action_id,user_id)',
         'Shortcut for this menu already exists!'),
    ]

    @api.model
    def get_user_shortcuts(self, domain):
        shortcuts = self.search([('user_id', '=', self.env.user.id)])
        res = []
        for shortcut in shortcuts.filtered('action_id'):
            _name = shortcut.action_id.with_context(lang=self.env.user.lang).name_get()
            _name = _name[0][1] if len(_name) else ''
            _id = shortcut.action_id.id
            _link = domain + '#' + shortcut.link
            res.append(
                {
                    'id': shortcut.id,
                    'name': _name,
                    'menu_id': (_id, _name),
                    'link': _link
                }
            )

        return res

    @api.model
    def check_if_bookmarked(self, action_id):
        res = []
        if action_id:
            bookmarked = self.search([('action_id', '=', int(action_id)), ('user_id', '=', self.env.user.id)])
            res.append({'class': 'oe_shortcut_toggle o_priority_star fa fa-star oe_shortcut_remove',
                        'action': action_id}) if bookmarked else res.append(
                {'class': 'oe_shortcut_toggle o_priority_star fa fa-star', 'action': action_id})
        else:
            res.append({'class': 'hidden', 'action': action_id})
        return res

    @api.model
    def remove_shortcut(self, action_id):
        bookmarked = self.search([('action_id', '=', int(action_id)), ('user_id', '=', self.env.user.id)])
        bookmarked.unlink()
        return bookmarked

    @api.model
    def create(self, vals):
        if 'link' in vals:
            vals_link = []
            for attr in vals['link'].split('&'):
                view = attr.split('=')
                if view[0] != 'id':
                    act_rec = self.env['ir.actions.act_window'].browse(int(vals['action_id']))
                    vals_link.append('view_type=%s' % act_rec.view_mode.split(',')[0] if view[1] == 'form' else attr)
            vals['link'] = '&'.join(vals_link) if vals_link else vals['link']
            return super(WebShortcut, self).create(vals)
        else:
            return self
