# -*- coding: utf-8 -*-
{
    'name': 'PO Exhaustion',
    'version': '18.0.1.0.0',
    'description': """ Customisation for PO Exhaustion """,
    'depends': ['base','sale_management'],
    'installable': True,

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/sale_order.xml',
    ],

}
