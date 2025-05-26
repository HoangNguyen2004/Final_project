{
    'name': 'Purchase Approval',
    'version': '1.0',
    'category': 'Purchases',
    'author': 'Group 6',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
