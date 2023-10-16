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

from openerp import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_code = fields.Char('BU Code for tax', default='0')

    code_for_refunds = fields.Char('BU Code for refunds', default='')