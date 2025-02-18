# -*- coding: utf-8 -*-

{
    'name': 'Contracts Management',
    'version': '18.0.1.0.0',
    'description': """ Contract Management """,
    'depends': ['base','mail'],
    'installable': True,

    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/contract_management.xml',
        'views/contract_management_tags.xml',
        'views/contract_management_state.xml',
        'views/menu.xml',

    ],
    "license": "LGPL-3",
    "application": True,

}
