import requests
from odoo import fields, models


class ZohoConnector(models.Model):
    _name = 'zoho.connector'
    _description = 'Zoho Connector'

    name = fields.Char('Instance Name', help='Instance Name')
    client_id = fields.Char('Client Id', help='Client Id of Zoho CRM',
                            required=True)
    client_secret = fields.Char('Client Secret',
                                help='Client Secret of Zoho CRM', required=True)
    refresh_token = fields.Char('Refresh Token',
                                help="Refresh Token of Zoho CRM", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("Connected", "Connected"), ("Failed", "Failed"),
         ('expired','Access Token Expired')],
        default="draft",
        string="State",
        help="State of the supply request.",
    )
    access_token = fields.Char("Access Token", help='Access token', readonly=True)
    company = fields.Many2one('res.company','Company', help='Choose the Company')


    def action_generate_access_token(self):
       url = "https://accounts.zoho.com/oauth/v2/token"
       client_id = self.client_id
       client_secret = self.client_secret
       refresh_token = self.refresh_token

       payload = f'grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}'
       headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
       }

       response = requests.request("POST", url, headers=headers, data=payload)
       data = response.json()
       self.write({
          'access_token': data['access_token'],
          'state': 'Connected',
       })

    def generate_access_token(self):
        instances = self.env['zoho.connector'].search([('state','=','Connected')])
        for instance in instances:
            url = "https://accounts.zoho.com/oauth/v2/token"
            client_id = instance.client_id
            client_secret = instance.client_secret
            refresh_token = instance.refresh_token

            payload = f'grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            data = response.json()
            instance.write({
                'access_token': data['access_token'],
                'state': 'Connected',
            })

    def action_fetch_emails(self, batch_size=15):

        # Fetch all contacts in Odoo with a Zoho Contact ID
        partners = self.env['res.partner'].search([
            ('company_id', '=', self.company.id),
            ('zoho_record_id', '!=', False)  # Ensure Zoho ID is available
        ])
        total_contacts = len(partners)
        for i in range(0, total_contacts, batch_size):
            batch_partners = partners[i:i + batch_size]
            zoho_partners = []
            for partner in batch_partners:
                zoho_partners.append(partner.id)
            queue = self.env['zoho.queue'].create({
                'name':f"Processing batch {i + 1} to {i + len(batch_partners)}",
                'action': 'Fetch Emails',
                'data': zoho_partners,
                'state':'draft',
                'instance_id':self.id,
                'company_id':self.company.id,
            })
