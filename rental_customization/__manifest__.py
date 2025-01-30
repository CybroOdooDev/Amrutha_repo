# -*- coding: utf-8 -*-
{
    'name': 'Rental Customization',
    'version': '18.0.1.0.0',
    'description': """ Customisation for Rental module """,
    'depends': ['base','product','sale_management', 'sale_project','sale_renting', 'account','sale_stock','stock'],
    'installable': True,

    'data': [
        'data/default_products.xml',
        'data/default_pricelist.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/ir_cron_data.xml',
        'data/paperformat.xml',
        'views/product_template.xml',
        'views/sale_order.xml',
        'views/recurring_plan.xml',
        'views/product_pricelist.xml',
        'views/res_config_settings.xml',
        'views/stock_lot.xml',
        'report/delivery_pdf_templates.xml',
        'report/pickup_pdf_templates.xml',
        'report/manage_reports_action.xml',
    ],

}
