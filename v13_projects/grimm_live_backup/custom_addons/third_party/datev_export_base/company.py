# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@openfellas.com
#
##############################################################################

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    consultant_number = fields.Char(string='Beraternummer', size=32, help="Number from 1000 to 9999999")
    client_number = fields.Char(string='Mandantennummer', size=32, help="Number from 0 to 99999")

    export_for_checked_or_not_checked_acc_bu_code_to_datev = fields.Boolean(string='Export checked or not checked', default=False, track_visibility='onchange', help="If flagged then export checked accounts otherwise export not cheked accounts!")
