{
    "name": "Document Management Module",
    "depends": ["base", 'crm', 'sign','commission_plan','account', 'product', 'stock', 'sale_management','purchase'],
    "category": "Sales/CRM",
    "version": "1.0",
    "data": [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/lead_document_views.xml',
        'views/sign_template_views.xml'
    ],
    "license": "LGPL-3",
    "summary": "Lange Real Estate (RE) Residential and Commercial "
               "Document Management and signature approval",
    "application": False,
    "installable": True,
}
