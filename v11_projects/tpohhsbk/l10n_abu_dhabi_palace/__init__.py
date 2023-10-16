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
    env.ref('l10n_abu_dhabi_palace.account_arabic_coa_abu_dhabi_palace').process_coa_translations()
