from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    zoho_record_reference = fields.Char('Zoho Id', help='Zoho record reference')
    deal_owner_id = fields.Many2one('res.users', string='Owner',
                                    help='Deal Owner')
    amount = fields.Float('Amount', help='Deal amount')
    business_type = fields.Char('Business Type', help='Type of Business')
    next_step = fields.Char('Next step', help='Next step')
    zoho_lead_source = fields.Char('Lead Source', help='Lead Source')
    zoho_lead_status= fields.Char('Lead Status', help='Lead Status')
    forcast_category = fields.Char('Forcast Category', help='Forcast Category')
    revenue = fields.Float('Revanue/Mo', help='Revanue/Mo')
    principle_reduction = fields.Float('Principal Reduction',
                                       help='Principal Reduction')
    deal_rate = fields.Char('Deal Rate', help='Deal Rate')
    lease_fee = fields.Char('Lease Fee', help='Lease Fee')
    lease_payment = fields.Char('Lease Payment', help='Lease Payment')
    lease_no = fields.Char('Lease Number', help='Lease No')
    term = fields.Char('Term', help='Term')
    industry = fields.Char('Industry', help='Industry')
    listed_title = fields.Char('Listed Title', help='Listed Title')
    mo_return_rate = fields.Char('Mo. Rate of Return',
                                 help='Mo. Rate of Return')
    initial_payment = fields.Char('Initial Payment', help='Initial Payment')
    date_reply_required = fields.Date('Date Reply Required',
                                      help='Date Reply Required')
    quote_description = fields.Char('Quote Description',
                                    help='Quote Description')
    accounting_status = fields.Char('Accounting Status',
                                    help='Accounting Status')
    residual_payment = fields.Char('Residual Payment', help='Residual Payment')
    lease_start_date = fields.Datetime('Lease Start Date',
                                       help='Lease Start Date')
    special_ach_pull_date = fields.Datetime('Special ACH Pull Date',
                                            help='Special ACH Pull Date')
    dealer = fields.Char('Dealer', help='Dealer')
    wire_sent_date = fields.Datetime('Wire Sent Date', help='Wire sent date')
    dealer_contact = fields.Char('Dealer Contact', help='Dealer Contact')
    dealer_phone = fields.Char('Dealer Phone Number',
                               help='Phone number of Dealer')
    dealer_email = fields.Char('Dealer email', help='email of Dealer')
    signing_status = fields.Char('Signing Status', help='Signing Status')
    funding_source = fields.Char('Funding Source', help='Funding Source')
    second_initial_payment = fields.Float('2nd Initial Payment',
                                          help='Amount of 2nd Initial Payment')
    invoice_amount = fields.Float('Invoice Amount',
                                  help='Invoice amount in Zoho')
    total_downpayment = fields.Float('Total Down payment',
                                     help='Total Down payment in Zoho')
    payment_due = fields.Char('Payment Due date', help='Payment Due date')
    lost_reason = fields.Char('Lost Reason', help='Lost Reason')
    business_name = fields.Char('Business name', help='Business Name')
    bank_rate = fields.Char('Bank Rate', help='Bank Rate')
    equipment = fields.Char('Equipment', help='Equipment')
    guarantor = fields.Char('Guarantor', help='Guarantor')
    quote_lease_fee = fields.Char('Quote Lease Fee', help='Quote Lease Fee')
    total_cost = fields.Char('Total Cost', help='Total Cost')
    quote_rate = fields.Char('Quote Rate', help='Quote Rate')
    quote_lease_term = fields.Char('Quote Lease Term', help='Quote Lease Term')
    quote_number_of_mon_down = fields.Float('Quote Number of Mon. Down',
                                            help='Quote Number of Mon. Down')
    quote_principal_reduction = fields.Float('Quote Principal Reduction',
                                             help='Quote Principal Reduction')
    quote_notes = fields.Char('Quote Notes', help='Quote Notes')
    quote_monthly_payment = fields.Float('Quote Monthly Payment',
                                         help='Quote Monthly Payment')
    quote_initial_payment = fields.Float('Quote Initial Payment',
                                         help='Quote Initial Payment')
    quote_total_receivable = fields.Float('Quote Total Receivable',
                                          help='Quote Total Receivable')
    quote_monthly_lease_spread = fields.Float('Quote Monthly Lease Spread',
                                              help='Quote Monthly Lease Spread')
    total_lease_profit = fields.Float('Total Lease Profit',
                                      help='Total Lease Profit')
    rate_of_return = fields.Float('Rate of Return', help='Rate of Return')
    insurance_expiration = fields.Datetime('Insurance Expiration',
                                           help='Insurance Expiration')
    insurance_expires = fields.Datetime('Insurance Expires',
                                        help='Insurance Expires')
    sales_tax = fields.Char('Sales Tax', help='Sales Tax')
    dealer_address = fields.Char('Dealer Address', help='Dealer Address')
    total_advance = fields.Char('Total Advance', help='Total Advance')
    total_mo_payment_including_tax = fields.Float(
        'Total Mo Payment Including Tax', help='Total Mo Payment Including Tax')
    serial_no = fields.Char('Serial No./VIN', help='Serial No./VIN')
    account_address = fields.Char('Account Address', help='Account Address')
    qty = fields.Char('QTY', help='QTY')
    make_model = fields.Char('Make/Model', help='Make/Model')
    internal_notes = fields.Html('Internal Notes', help='Internal Notes')

    zoho_lead_company = fields.Char('Company', help='Company')
    title_zoho = fields.Char('Title', help='Title of Zoho lead')
    street = fields.Char("street", help='street')
    city = fields.Char("City", help='City')
    state_id = fields.Many2one("res.country.state", help='State',
                               string='State')
    zip = fields.Char("Zip Code", help='Zip Code')
    country_id = fields.Many2one("res.country", help='Country',
                                 string='Country')
    how_did_you_hear_about_us = fields.Char('How did you hear about us?',
                                            help='How did you hear about us?')
    which_product_are_you_intrested_in = fields.Char(
        'Which product(s) are you interested in?',
        help='Which product(s) are you interested in?')
    comments = fields.Char('Comments', help='Comments')
    unsubscribed_mode = fields.Char('Unsubscribed Mode',
                                    help='Unsubscribed Mode')
    unsubscribed_time = fields.Datetime('Unsubscribed Time',
                                        help='Unsubscribed Time')
    do_not_use = fields.Char('DO NOT USE', help='DO NOT USE')
    url = fields.Char('URL 1', help='URL 1')
    lead_outcome = fields.Char('Lead Outcome', help='Lead Outcome')
    roofing_component_interested = fields.Char(
        'What roofing components are you interested in?',
        help='What roofing components are you interested in?')
    building_component_interested = fields.Char(
        'What building components are you interested in?',
        help='What building components are you interested in?')
    lead_origin = fields.Char('Lead Origin (Site)', help='Lead Origin (Site)')
    how_can_help = fields.Char('How Can We Help?', help='How Can We Help?')
    interested_product = fields.Char('What products are you interested in?',
                                     help='What products are you interested in?')
    lead_notes = fields.Char('LEADS NOTES', help='LEADS NOTES')
    original_lead_source = fields.Char('Original Lead Source',help='Original Lead Source')
    gclid = fields.Char('GCLID', help='GCLID')
    compaignid = fields.Char('ZCAMPAIGNID',help='ZCAMPAIGNID')
    adgroupid = fields.Char('ADGROUPID',help='ADGROUPID')
    adid = fields.Char('ADID', help='ADID')
    keywordid = fields.Char('KEYWORDID', help='KEYWORDID')
    Keyword = fields.Char('Keyword', help='Keyword')
    click_type = fields.Char('Click Type', help='Click Type')
    device_type = fields.Char('Device Type', help='Device Type')
    ad_network = fields.Char('Ad Network', help='Ad Network')
    ad_compaign_name = fields.Char('Ad Campaign Name', help='Ad Campaign Name')
    ad_group_name = fields.Char('AdGroup Name', help='AdGroup Name')
    ad = fields.Char('Ad', help='Ad')
    gadconfigid = fields.Char('GADCONFIGID', help='GADCONFIGID')
    annual_revenue = fields.Float('Annual Revenue', help='Annual Revenue')
    employee_count = fields.Integer('No. of Employees', help='No. of Employees')
    visit_score = fields.Float('Visitor Score', help='Visitor Score')
    state_of_business_registration = fields.Many2one('res.country.state',
                                                      'State of Business Registration',
                                                      help='State of Business Registration')
    years_in_business = fields.Char('Years in Business', help='Years in Business')
    fien_name = fields.Char('Federal Employer Identification Number (FIEN)',
                            help='Federal Employer Identification Number (FIEN)')
    equipment_cost = fields.Char('Equipment Cost', help='Equipment Cost')
    equipment_dealer = fields.Char('Equipment Dealer',help='Equipment Dealer')
    additional_comments = fields.Text('Additional Comments',help='Additional Comments')
    equipment_dealer_phone_number = fields.Char('Equipment Dealer Phone Number',
                                                help='Equipment Dealer Phone Number')
    type_of_business_filing = fields.Char('Type of Business Filing', help='Type of Business Filing')
    social_security_number = fields.Char('Social Security Number', help='Social Security Number')
    business_address = fields.Char('Business Address', help='Business Address')
    equipment_description = fields.Char('Equipment Description', help='Equipment Description')



