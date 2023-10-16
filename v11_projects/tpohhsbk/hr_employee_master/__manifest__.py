{
    'name': 'EMP',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Employee',
    'description':  """**********Employee***********
            This is EMP Module for inherit Employee Details.
    """,
    'website': 'www.bistasolutions.com',
    'depends': ['base','hr','contacts'],
    'data': [
        'views/employee_view.xml',

    ],
    'installable': True,
    'application': False,
    'auto-install':False,

}