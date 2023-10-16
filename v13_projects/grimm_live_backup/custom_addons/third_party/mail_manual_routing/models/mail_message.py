# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class mail_message(models.Model):
    """
    Overwrite to introduce re-routing methods
    """
    _inherit = "mail.message"

    is_unattached = fields.Boolean(string="Unattached message")

    def action_attach(self):
        """
        Method to return 'attach message wizard'

        Returns:
         * aciton dict
        """
        return {
            'name': _("Route Message"),
            'res_model': 'mail.message.attach.wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message_ids': [(6, 0, self.ids)],
            },
        }
        
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Overwrite to provide the access for the admin rights with the settings (not only SuperUser)
        """
        if self.env.context.get("unattached_interface") and (self.env.user.has_group("base.group_system") \
                or self.env.user.has_group("mail_manual_routing.group_lost_messages")):
            res = super(mail_message, self.sudo())._search(args=args, offset=offset, limit=limit, order=order,
                                                          count=count, access_rights_uid=access_rights_uid,)
        else:
            res = super(mail_message, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                        access_rights_uid=access_rights_uid,)
        return res

    def check_access_rule(self, operation):
        """
        Overwrite to provide the access for the admin rights with the settings (not only SuperUser)
        """
        if self.env.user.has_group("base.group_system") \
                or self.env.user.has_group("mail_manual_routing.group_lost_messages"):
            return
        super(mail_message, self).check_access_rule(operation=operation)
