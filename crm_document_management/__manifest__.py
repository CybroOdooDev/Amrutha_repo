{
    "name": "Document Management Module",
    "depends": ["base", 'crm', 'sign', 'commission_plan', 'account', 'product',
                'stock', 'sale_management', 'purchase','mail', 'attachment_indexation', 'portal', 'sms'],
    "category": "Sales/CRM",
    "version": "1.0",
    'author': 'The Lange Companies',
    "data": [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/lead_document_views.xml',
        'views/sign_template_views.xml',
        'views/sign_template_tag_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_document_management/static/src/components/sign_request/signable_PDF_iframe.js',
        ],
        'web.assets_frontend': [
            'crm_document_management/static/src/components/sign_request/signable_PDF_iframe.js',
        ],
        'sign.assets_public_sign': [
            'crm_document_management/static/src/components/sign_request/signable_PDF_iframe.js',
        ],
    },
    "license": "LGPL-3",
    "summary": "Lange Real Estate (RE) Residential and Commercial "
               "Document Management and signature approval",
    "application": False,
    "installable": True,
}
