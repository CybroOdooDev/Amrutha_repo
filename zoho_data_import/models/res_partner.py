from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_owner_id = fields.Many2one('res.users', 'Contact Owner',
                                       help='Related Owner of Contact')
    zoho_record_id = fields.Char('Zoho Contact Reference', help='Record reference in Zoho')

    # title = fields.Char('Zoho Title', help='Title of Contacts in Zoho')
    home_phone = fields.Char('Home phone', help='Home Phone')
    other_phone = fields.Char('Other phone', help='Other Phone')
    birth_date = fields.Date(string='Date of Birth',
                             help='Date of Birth of Contacts')
    assistant = fields.Char('Assistant', help='Contact Assistant')
    mailing_street = fields.Char('Mailing Street',
                                 help='Mailing Street of Contact')
    other_street = fields.Char('Other Street', help='Other Street of Contact')
    mailing_city = fields.Char('Mailing City', help='Mailing City of Contact')
    other_city = fields.Char('Other City', help='Other City of Contact')
    mailing_state_id = fields.Many2one('res.country.state', 'Mailing State',
                                    help='Mailing state of Contact')
    other_state_id = fields.Many2one('res.country.state', 'Other State',
                                  help='Other state of Contact')
    mailing_zip = fields.Char('Mailing Zip', help='Mailing Zip of Contact')
    other_zip = fields.Char('Other Zip', help='Other Zip of Contact')
    mailing_country_id = fields.Many2one('res.country',
                                      help='Mailing country of Contact')
    other_country_id = fields.Many2one('res.country',
                                    help='Other country of Contact')
    description = fields.Char('Description', help='Zoho description of Contact')
    salutation = fields.Char('Salutation', help='Salutation of Contact')
    secondary_email = fields.Char('Secondary Email',
                                  help='Secondary Email of Contatct')
    tag = fields.Char(string='Tag', help='Contact Tag')
    residence_zip = fields.Char(string='Residence Zip',
                                help='Residance Zip of Contact')
    notes = fields.Char(string='Zoho Notes', help='Notes')
    subject = fields.Char('Subject', help='Subject')
    business_type = fields.Char('Type of Business', help='Type of Business')
    bussiness_state_id = fields.Many2one('res.country.state',
                                      string='State of Business Registration')
    fien_number = fields.Char('Federal Employer Identification Number (FIEN)',
                              help='Federal Employer Identification Number (FIEN)')
    bussiness_street_address = fields.Char('Business Street Address',
                                           help='Business Street Address')
    time_in_business = fields.Char('Time in Business', help='Time in Business')
    industry_experience = fields.Float('Industry Experience (years)',
                                       help='Industry Experience (years)')
    annual_revanue = fields.Char('Annual Revenue', help='Annual Revenue')
    employee_count = fields.Char('Number of Employees',
                                 help='Number of Employees')
    owner_legal_name = fields.Char("Guarantor/Owner's Full Legal Name",
                                   help="Guarantor/Owner's Full Legal Name")
    social_security_number = fields.Char('Social Security Number')
    residence_address = fields.Char('Residence Address')
    residance_state_id = fields.Many2one('res.country.state', 'Residence State')
    residance_city = fields.Char('Residence City')
    business_zip = fields.Char('Business zip')
    equipment_description = fields.Char('Equipment Description')
    equipment_cost = fields.Char('Equipment Cost')
    equipment_dealer = fields.Char('Equipment Dealer')
    equipment_dealer_contact = fields.Char('Equipment Dealer Contact')
    equipment_dealer_phone = fields.Char('Equipment Dealer Phone')
    preferred_name = fields.Char('Preferred Name')
    industry = fields.Char('Industry Drop Down')
    account_owner_id = fields.Many2one('res.users', string='Account Owner',
                                       help="Related Account Owner of Contact")
    account_site = fields.Char('Account Site', help="Account Site of Contact")
    fax = fields.Char('Fax', help="fax")
    account_type = fields.Char('Account Type', help="Account Type")
    ownership = fields.Char('Ownership', help="Ownership")
    sic_code = fields.Char('SIC Code', help="SIC Code")
    billing_street = fields.Char('Billing Street', help="Billing Street")
    shipping_street = fields.Char('Shipping Street', help="Shipping Street")
    billing_city = fields.Char('Billing City', help="Billing City")
    shipping_city = fields.Char('Shipping City', help="Shipping City")
    billing_state_id = fields.Many2one('res.country.state', 'Billing State')
    shipping_state_id = fields.Many2one('res.country.state', 'Shipping State')
    billing_code =  fields.Char('Billing Code', help="Billing Code")
    shipping_code =  fields.Char('Shipping Code', help="Shipping Code")
    billing_country_id = fields.Many2one('res.country',
                                      help='Billing country of Contact')
    shipping_country_id = fields.Many2one('res.country',
                                      help='Shipping country of Contact')

