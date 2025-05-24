{
    'name': 'Purchase Request',
    'version': '1.0',
    'category': 'Purchases',
    'author': 'Group_6',
    'depends': ['purchase', 'purchase_approval'],
    'data': [
        'data/purchase_request_sequence.xml',
        'security/ir.model.access.csv',
        'views/purchase_request_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
