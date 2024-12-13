# -*- coding: utf-8 -*-
{
    'name': "ABS Finance",
    'summary': """Module Kế Toán""",
    'description': """Module Kế Toán""",
    'author': "AUM ITC",
    'category': 'AUM Business System/ Finance',
    'website': 'https://aum.edu.vn/',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_payment',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/th_finance_security.xml',
        'data/ir_sequence.xml',
        'views/th_internal_transfer_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
