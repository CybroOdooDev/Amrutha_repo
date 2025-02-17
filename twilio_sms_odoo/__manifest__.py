{
    'name' : 'Twilio SMS Odoo- Send & Receive',
    "summary": "Send & Receive SMS using Twilio SMS Gateway",
    "description": "The Twilio SMS Odoo module facilitates the effortless dispatch of outgoing messages to your clientele, prospects, and other pertinent contacts. Moreover, it enables the efficient monitoring of inbound messages within the Odoo platform.",
    'version' : '18.0.1.0.0',
    'module_type': 'official',
    'category' : 'SMS',
    'sequence' : 1,
    "website": "https://www.cirantait.com/",
    "company": "Ciranta IT Services Pvt Ltd",
    "support": "odooapps@deskcirantait.odoo.com",
    "author": "Ciranta IT Services",
    "license": "OPL-1",
    "depends": ['crm','phone_validation','mass_mailing_sms','sms'],
    "price": "15.00",
    "currency": "USD",
    "data": [
    'security/ir.model.access.csv',
    "views/sms.xml",
         "views/mail_template.xml",
    ],
    'installable' : True,
    'application' : True,
    'auto_install' : False,
    'images': ['static/description/banner.png'],
}



