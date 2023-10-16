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
    'name': 'GRIMM GTEG Import Invoice',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'GTEG Import Invoice',
    'description': """
        Main purpose of this module is to create vendor bill using import EDI file.
    """,
    'depends': [
        'base',
        'sale',
        # 'grimm_reports',
        'fetchmail',
        #'web_notify',
        'purchase',
        'grimm_magentoerpconnect'
    ],
    'data': [
        'views/gteg_import_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
