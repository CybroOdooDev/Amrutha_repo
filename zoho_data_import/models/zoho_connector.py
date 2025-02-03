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
       print(data)
       print(data['access_token'])
       self.write({
          'access_token': data['access_token'],
          'state': 'Connected',
       })


       print(response.text)

    def generate_access_token(self):
        print('Haillll')
        instances = self.env['zoho.connector'].search([('state','=','Connected')])
        print('instances',instances)
        for instance in instances:
            print(instance)
            url = "https://accounts.zoho.com/oauth/v2/token"
            client_id = instance.client_id
            client_secret = instance.client_secret
            refresh_token = instance.refresh_token

            payload = f'grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                # 'Cookie': '_zcsr_tmp=47a0ce0c-e237-45ff-85b7-f63100061532; iamcsr=47a0ce0c-e237-45ff-85b7-f63100061532; zalb_b266a5bf57=4b43c140e1ec5ec8cfb85877989abc5e'
            }

            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            data = response.json()
            print(data)
            print(data['access_token'])
            instance.write({
                'access_token': data['access_token'],
                'state': 'Connected',
            })

    def action_fetch_emails(self, batch_size=15):
        print("Fetching Emails from Zoho CRM in Batches...")

        # Fetch all contacts in Odoo with a Zoho Contact ID
        partners = self.env['res.partner'].search([
            ('company_id', '=', self.company.id),
            ('zoho_record_id', '!=', False)  # Ensure Zoho ID is available
        ])
        print('partners',partners)

        total_contacts = len(partners)
        print(f'Total partners to process: {total_contacts}')

        for i in range(0, total_contacts, batch_size):
            batch_partners = partners[i:i + batch_size]
            print('batch_partners',batch_partners)
            print(f"Processing batch {i + 1} to {i + len(batch_partners)}")
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
            print('queue',queue)

                # url = f"https://www.zohoapis.com/crm/v7/Contacts/{partner.zoho_contact_id}/Emails"
                #
                # headers = {
                #     'Authorization': f'Bearer {self.access_token}',
                #     'Content-Type': 'application/json'
                # }
                #
                # response = requests.get(url, headers=headers)
            #
            #     if response.status_code == 200:
            #         data = response.json()
            #
            #         if 'Emails' in data and data['Emails']:
            #             emails = [email['Email'] for email in data['Emails']]
            #             primary_email = emails[0]  # Use the first email as primary
            #
            #             # Update email in Odoo
            #             partner.write({'email': primary_email})
            #             print(f"Updated {partner.name} with email: {primary_email}")
            #         else:
            #             print(f"No emails found for {partner.name}")
            #     else:
            #         print(f"Failed to fetch emails for {partner.name}. Error: {response.text}")

            # Add a delay if needed to avoid API rate limits
            # self.env.cr.commit()  # Commit after each batch
            # print(f"Batch {i + 1} processed successfully.")

        # print("Email fetching process completed!")



