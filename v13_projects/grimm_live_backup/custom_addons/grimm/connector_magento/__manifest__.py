# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Magento Connector',
 'version': '11.0.1.0.0',
 'category': 'Connector',
 'depends': ['account',
             'base_technical_user',
             'product',
             'delivery',
             'sale_stock',
             'product_multi_category',
             'connector_ecommerce',
             #'connector_base_product',
             'grimm_pricelist',
             ],
 'external_dependencies': {
     'python': ['magento'],
 },
 'author': "Camptocamp,Akretion,Sodexis,Odoo Community Association (OCA)",
 'license': 'AGPL-3',
 'website': 'http://www.odoo-magento-connector.com',
 'images': ['images/magento_backend.png',
            'images/jobs.png',
            'images/product_binding.png',
            'images/invoice_binding.png',
            'images/connector_magento.png',
            ],
 'data': ['data/connector_magento_data.xml',
          'security/ir.model.access.csv',
          'views/magento_backend_views.xml',
          'views/product_views.xml', #Odoo13Change
          #'views/product_category_views.xml', #Odoo15Change
          'views/partner_views.xml',
          #'views/invoice_views.xml', #Odoo15Change
          'views/sale_order_views.xml',
          'views/connector_magento_menu.xml',
          'views/delivery_views.xml',
          'views/stock_views.xml',
          'views/account_payment_mode_views.xml',
          'wizards/magento_binding_backend_read.xml',
          ],
 'installable': True,
 'application': False,
 }
