{
    'name': 'Zoho Data Import',
    'version': '18.0.1.0.2',
    'depends':['base','base_setup','contacts','crm','mail','sale'],
    'data':{
        # 'security/contact_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/mail_views.xml',
        'views/zoho_connector_views.xml',
        'views/zoho_queue_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
    }
}
