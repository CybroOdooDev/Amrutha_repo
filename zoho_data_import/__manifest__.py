{
    'name': 'Zoho Data Import',
    'version': '18.0.1.0.1',
    'depends':['base','base_setup','contacts','crm','mail','sale'],
    'data':{
        # 'security/contact_security.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/mail_views.xml',
        'views/zoho_connector_views.xml',
        'views/products_template_views.xml',
        'views/sale_order_views.xml',
    }
}
