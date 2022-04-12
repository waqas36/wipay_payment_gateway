# -*- coding: utf-8 -*-
{
    'name': "WiPay Payment Gateway",

    'summary': """
        We've simplified the payment process To Grow your business by expanding into new markets.""",

    'description': """
        We've simplified the payment process To Grow your business by <br/> expanding into new markets.
    """,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'payment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'demo/payment_acquirer_data.xml',
        'views/payment.xml',
        'views/payment_transaction.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    # Author
    'author': 'Index World',
    'website': 'https://indexworld.net/',
    'maintainer': 'Index World',

    # Technical
    'price': 200,
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
