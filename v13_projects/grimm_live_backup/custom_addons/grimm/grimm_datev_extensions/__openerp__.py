# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'GRIMM DATEV Extensions',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': 'Grimm DATEV Extensions',
    'description': """
        Main purpose of this module is to enhance the DATEV functionality.
    """,
    'depends': ['base', 'datev_export'],
    'data': [
        'security/ir.model.access.csv',
        'views/datev_export_history_view.xml',
        'views/invoice_ledger_export_view.xml',
        'views/account_move_view.xml',
        'views/mail_template_view.xml',
    ],
    'installable': True,
    'qweb': [],
}
