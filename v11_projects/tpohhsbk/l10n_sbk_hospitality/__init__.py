# -*- coding: utf-8 -*-
##############################################################################
#
#  Bista Solutions Inc.
#  Website: https://www.bistasolutions.com
#
##############################################################################

from odoo import api, SUPERUSER_ID

def load_translations(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('l10n_sbk_hospitality.account_arabic_coa_sbk_hospitality').process_coa_translations()
