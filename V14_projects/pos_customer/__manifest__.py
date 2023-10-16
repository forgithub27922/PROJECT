# -*- coding: utf-8 -*-

# Copyright (C) 2019 Skyscend Business Solutions (<http://skyscendbs.com>)
# Copyright (C) 2020 Skyscend Business Solutions  Pvt. Ltd.(<http://skyscendbs.com>)

{
    'name': 'Pos Customer Filter',
    'category': 'Point of sale',
    'version': '14.0.0.1',
    'license': 'AGPL-3',
    'description': """
      Display only Customer in Pos Terminal.
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/partner.xml',
        'views/templates.xml'
    ],
    'installable': True,
}
