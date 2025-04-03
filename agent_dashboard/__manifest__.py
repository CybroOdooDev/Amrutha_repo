{
    'name': 'Agent Dashboard',
    'version': '1.0',
    'summary': 'CRM Dashboard for Agent',
    'description': 'A comprehensive dashboard for CRM operations.',
    'author': 'Renu M',
    'depends': ['base', 'crm', 'web',
                'spreadsheet_dashboard_account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/crm_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js',
            'agent_dashboard/static/src/js/crm_dashboard.js',
            'agent_dashboard/static/src/js/PieChart.js',
            'agent_dashboard/static/src/js/GoalVsActualChart.js',
            'agent_dashboard/static/src/xml/crm_dashboard.xml',
            'agent_dashboard/static/src/scss/crm_dashboard.scss',
            'agent_dashboard/static/src/js/business_summary_dashboard.js',
            'agent_dashboard/static/src/xml/business_summary_dashboard.xml',
            'agent_dashboard/static/src/scss/business_summary_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
}
