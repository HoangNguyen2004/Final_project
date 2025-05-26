{
    'name': 'Intercompany Transaction',
    'version': '18.0.1.0.1',
    'summary': 'Automatically create SO from PO between companies',
    'author': 'Group 6',
    'depends': [
        'purchase',
        'sale_management',
        'stock',
        'account',
    ],
    'data': [
        'views/res_company_views.xml',
        'views/intercompany_transaction_views.xml',
        'security/ir.model.access.csv',
        'data/intercompany_transaction_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'intercompany_transaction/static/src/js/intercompany_widget.js',
        ],
    },
}
