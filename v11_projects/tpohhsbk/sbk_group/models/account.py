# -*- coding: utf-8 -*-
##############################################################################
#
#  Bista Solutions Inc.
#  Website: https://www.bistasolutions.com
#
##############################################################################

from odoo import api, fields, models, _


class AccountGroup(models.Model):
    _inherit = "account.group"
    _order = 'sequence'

    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of Projects.")


class AccountAccount(models.Model):
    _inherit = "account.account"
    _order = "group_sequence,code"

    group_sequence = fields.Integer(related="group_id.sequence",
                                    string='Group Sequence',
                                    store=True)
