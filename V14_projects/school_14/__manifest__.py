{
    'name': 'School Management',
    'description': 'A module used to manage school',
    'version': '1.0',
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'www.skyscendbs.com',
    'depends': ['base'],
    'data': [
        'security/school_security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/student_view.xml',
        'data/student_sequence.xml',
    ],
    'auto_install': False,
    'application': True
}