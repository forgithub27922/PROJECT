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
    'name': 'GRIMM Ebay Extensions',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    'category': 'Connector',
    'summary': 'Extension of Ebay connector based on Grimm requirement.',
    'description': """
        Main purpose of this module is to enhance base Ebay connector to configure Multi account, ebay price based on pricelist.
    """,
    'depends': ['base', 'sale', 'sale_ebay', 'grimm_product_ruleset'],
    'data': [
        'views/product_view.xml',
        'views/ebay_backend_view.xml',
        'views/ir_cron_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'qweb': [],
}
