{
    'name': 'Dispatch Schedule Report',
    'version': '18.0.1.0.0',
    "license": "LGPL-3",
    'description': """ Dispatch schedule report for Sale and Rental Orders """,
    'depends': ['base', 'product', 'sale_management', 'rental_customization','web'],
    'data': [
        'views/product_views.xml',
        'views/product_return_dates.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dispatch_schedule_report/static/src/**/*',
        ]
    },

}
