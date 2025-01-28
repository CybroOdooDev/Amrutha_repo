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
       print("TESTTTTTT")
       url = "https://accounts.zoho.com/oauth/v2/token"
       print('self',self.read())
       client_id = self.client_id
       client_secret = self.client_secret
       refresh_token = self.refresh_token

       payload = f'grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}'
       headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          # 'Cookie': '_zcsr_tmp=47a0ce0c-e237-45ff-85b7-f63100061532; iamcsr=47a0ce0c-e237-45ff-85b7-f63100061532; zalb_b266a5bf57=4b43c140e1ec5ec8cfb85877989abc5e'
       }

       response = requests.request("POST", url, headers=headers, data=payload)
       data = response.json()
       print(data['access_token'])
       self.write({
          'access_token': data['access_token'],
          'state': 'Connected',
       })


       print(response.text)

    def action_fetch_emails(self):
        print("Fetch Emails")
        url = "https://www.zohoapis.com/crm/v7/Contacts/4260190000000266514/Emails/d9672d1431367c4210c326fb52e8893405d453c556d0acceaf1061e7ea4589ab"

        payload = {}
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            # 'Cookie': '_zcsr_tmp=b39af520-5917-4d71-91ef-05b95c7cd895; crmcsr=b39af520-5917-4d71-91ef-05b95c7cd895; group_name=usergroup1; zalb_1ccad04dca=a86c270747ff9c8bb9884cfcd1e7462d'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.json())



