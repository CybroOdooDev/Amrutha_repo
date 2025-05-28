{
    "name": "Payout approval",
    "depends": ["base", 'crm', 'sign', 'commission_plan', 'account', 'product',
                'stock', 'sale_management', 'purchase'],
    "category": "Sales/CRM",
    "version": '18.0.1.0.0',
    'author': 'The Lange Companies',
    "data": [
        'security/ir.model.access.csv',
        'data/approval_sign_data.xml',
        'data/product_product_data.xml',
        'views/crm_lead_views.xml',
        'views/res_user_views.xml',
        'wizard/signature_request_wizard.xml',

    ],
    "license": "LGPL-3",
    "summary": "Lange Real Estate (RE) Residential and Commercial "
               "Commissions Payout Sign Approval",
    "application": False,
    "installable": True,
}
