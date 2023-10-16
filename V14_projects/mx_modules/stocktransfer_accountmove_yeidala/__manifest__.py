# -*- coding: utf-8 -*-
{
    'name': "Stock Internal Transfer Account Move",
    'summary': """Modulo para agregar cuenta analitica en almacen""",
    'description': """
Cambios en Modulo.
========================

1. Cuentas analiticas: Se agrega cuenta analitica en almacen
2. Se crea proceso para generar asientos de costos de "Transferencias Internas"
3. Se crea proceso para agregar cuentas analiticas en asientos de Valoración de Inventarios
""",
    'author': "Yeidala",
    'website': "https://yeidala.odoo.com",
    'category': 'Uncategorized',
    'version': '1.0.8',
    'depends': ['base_setup', 'stock', 'account', 'sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stock_models_views.xml',
    ]
}
