# -*- coding: utf-8 -*-


{
    "name": "Openfellas Block Customer",
    "version": "13.0.1.0",
    "summary": "Openfellas Block Customer",
    "depends": [
        'sale',
    ],
    "author": "openfellas, Viet Pham",
    "category": "Sale",
    "description": """
        This module allows to block the validation of a Sale Order and Deliveries
        for selected customers.
    """,
    "data": [
        'security/ir.model.access.csv',
        'security/sale_block_security.xml',
        'data/sale_block_reason_data.xml',
        'views/res_partner_view.xml',
        'views/sale_block_reason_view.xml',
        'views/sale_order_view.xml'
    ],
    "qweb": [],

}
