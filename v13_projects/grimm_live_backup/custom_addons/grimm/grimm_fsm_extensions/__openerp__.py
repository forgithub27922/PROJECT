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
    'name': 'GRIMM FSM Extensions',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Field Service',
    'summary': 'Grimm Field Service Management Extensions',
    'description': """
        Main purpose of this module is to enhance the Field service management functionality.
    """,
    'depends': ['base', 'industry_fsm', 'industry_fsm_report', 'grimm_mobile_barcode_scan', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_view.xml',
        'views/project_project_view.xml',
        'views/bornemann_config_view.xml',
        'views/worksheet_custom_report_templates_inherit.xml',
        'views/template.xml',
    ],
    'installable': True,
    'qweb': [
        "static/src/xml/kanban_view.xml",
    ],
}
