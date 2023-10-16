# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from binascii import Error as binascii_error
from collections import defaultdict
from operator import itemgetter
from odoo.http import request

from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import groupby
class Message(models.Model):
    _inherit = 'mail.message'

    parent_reply_id = fields.Many2one('mail.message', 'Parent Reply Message', ondelete='set null')

    @api.model
    def default_get(self, fields):
        result = super(Message, self).default_get(fields)
        return result

    def _get_message_format_fields(self):
        return [
            'id', 'body', 'date', 'author_id', 'email_from',  # base message fields
            'message_type', 'subtype_id', 'subject',  # message specific
            'model', 'res_id', 'record_name',  # document related
            'channel_ids', 'partner_ids',  # recipients
            'starred_partner_ids',  # list of partner ids for whom the message is starred
            'moderation_status',
            'notified_partner_ids',
            'parent_reply_id'
        ]

    # def message_format(self):
    #     """ Get the message values in the format for web client. Since message values can be broadcasted,
    #         computed fields MUST NOT BE READ and broadcasted.
    #         :returns list(dict).
    #          Example :
    #             {
    #                 'body': HTML content of the message
    #                 'model': u'res.partner',
    #                 'record_name': u'Agrolait',
    #                 'attachment_ids': [
    #                     {
    #                         'file_type_icon': u'webimage',
    #                         'id': 45,
    #                         'name': u'sample.png',
    #                         'filename': u'sample.png'
    #                     }
    #                 ],
    #                 'needaction_partner_ids': [], # list of partner ids
    #                 'res_id': 7,
    #                 'tracking_value_ids': [
    #                     {
    #                         'old_value': "",
    #                         'changed_field': "Customer",
    #                         'id': 2965,
    #                         'new_value': "Axelor"
    #                     }
    #                 ],
    #                 'author_id': (3, u'Administrator'),
    #                 'email_from': 'sacha@pokemon.com' # email address or False
    #                 'subtype_id': (1, u'Discussions'),
    #                 'channel_ids': [], # list of channel ids
    #                 'date': '2015-06-30 08:22:33',
    #                 'partner_ids': [[7, "Sacha Du Bourg-Palette"]], # list of partner name_get
    #                 'message_type': u'comment',
    #                 'id': 59,
    #                 'subject': False
    #                 'is_note': True # only if the message is a note (subtype == note)
    #                 'is_discussion': False # only if the message is a discussion (subtype == discussion)
    #                 'is_notification': False # only if the message is a note but is a notification aka not linked to a document like assignation
    #                 'moderation_status': 'pending_moderation'
    #             }
    #     """
    #     message_values = self.read(self._get_message_format_fields())
    #     message_tree = dict((m.id, m) for m in self.sudo())
    #     self._message_read_dict_postprocess(message_values, message_tree)
    #
    #     # add subtype data (is_note flag, is_discussion flag , subtype_description). Do it as sudo
    #     # because portal / public may have to look for internal subtypes
    #     subtype_ids = [msg['subtype_id'][0] for msg in message_values if msg['subtype_id']]
    #     subtypes = self.env['mail.message.subtype'].sudo().browse(subtype_ids).read(['internal', 'description', 'id'])
    #     subtypes_dict = dict((subtype['id'], subtype) for subtype in subtypes)
    #
    #     com_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment')
    #     note_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note')
    #
    #     # fetch notification status
    #
    #     notif_dict = defaultdict(lambda: defaultdict(list))
    #     notifs = self.env['mail.notification'].sudo().search(
    #         [('mail_message_id', 'in', list(mid for mid in message_tree)), ('res_partner_id', '!=', False)])
    #
    #     for notif in notifs:
    #         mid = notif.mail_message_id.id
    #         if notif.is_read:
    #             notif_dict[mid]['history_partner_ids'].append(notif.res_partner_id.id)
    #         else:
    #             notif_dict[mid]['needaction_partner_ids'].append(notif.res_partner_id.id)
    #
    #     for message in message_values:
    #         message['needaction_partner_ids'] = notif_dict[message['id']]['needaction_partner_ids']
    #         message['history_partner_ids'] = notif_dict[message['id']]['history_partner_ids']
    #         message['is_note'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['id'] == note_id
    #         message['is_discussion'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['id'] == com_id
    #
    #
    #         message['subtype_description'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['description']
    #         message['is_notification'] = message['message_type'] == 'user_notification'
    #
    #         if message['model'] and self.env[message['model']]._original_module:
    #             message['module_icon'] = modules.module.get_module_icon(self.env[message['model']]._original_module)
    #     ### Needs to pass ['needaction_partner_ids', 'history_partner_ids', 'is_discussion']
    #     return message_values