{
    'name': 'Agent Dashboard',
    'version': '1.0',
    'summary': 'CRM Dashboard for Agent',
    'description': 'A comprehensive dashboard for CRM operations.',
    'author': 'Renu M',
    'depends': ['crm','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'agent_dashboard/static/src/js/crm_dashboard.js',
            'agent_dashboard/static/src/xml/crm_dashboard.xml',
            'agent_dashboard/static/src/scss/crm_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
}