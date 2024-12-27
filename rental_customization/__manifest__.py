{
    'name': 'Rental Customization',
    'version': '18.0.1.0.0',
    'description': """ Customisation for Rental module""",
    'depends': ['base','product','sale_management', 'sale_project', 'account'],
    'installable': True,

    'data': [
        'data/default_products.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/ir_cron_data.xml',
        'views/product_template.xml',
        'views/sale_order.xml',
        'views/recurring_plan.xml',
    ],

}
