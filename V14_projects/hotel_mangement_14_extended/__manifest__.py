{
    'name': 'Hotel Management Extended',
    'description': 'An extended module of hotel management',
    'version': '1,0',
    'author': 'Skyscend Business Solution Pvt.Ltd.',
    'website': 'www.skyscendbs.com',
    'depends': ['hotel_mangement_14'],
    'data': [
        'security/customer_security.xml',
        'security/ir.models.access.csv',
        'views/customer_view.xml',
        'views/customer_room_view.xml',
        'views/customer_city_view.xml',
        'views/customer_room_amenities.xml',
        'views/customer_room_products.xml',
        'report/customer_analysis_report.xml',
        'wizard/update_age_wiz_view.xml',
        'report/report_customer_template.xml',
        'report/hotel_report.xml',


    ],
    'auto-install': False,
    'application': True

}
