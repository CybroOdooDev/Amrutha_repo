import logging
import requests
from odoo import api, fields, models
_logger = logging.getLogger(__name__)
from odoo.fields import Datetime


class ZohoQueue(models.Model):
    _name = 'zoho.queue'
    _description = 'Zoho Queue'

    name = fields.Char('Name', help='Name of Queue')
    action = fields.Char('Action', help='Action need to perform')
    data = fields.Json('Data', help='Content of Data')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', help="state of Queue"
    )
    instance_id = fields.Many2one('zoho.connector', help='Zoho Instance')
    company_id = fields.Many2one('res.company','Company')

    def action_sync_zoho_emails(self):
        print('kkkkk',self)
        job = self.env['zoho.queue'].sudo().search([('state', '=', 'draft')],
                                                   order='id asc', limit=1)
        print('job',job)
        if job:
            # print('llll', job.data)
            try:
                for partner in job.data:
                    partner_id = self.env['res.partner'].browse(partner)
                    # print('contact', partner_id, partner_id.zoho_record_id)
                    zoho_id = partner_id.zoho_record_id.replace("zcrm_", "")
                    # print('zoho_id', zoho_id)
                    url = f"https://www.zohoapis.com/crm/v7/Contacts/{zoho_id}/Emails"

                    headers = {
                        'Authorization': f'Bearer {job.instance_id.access_token}',
                        'Content-Type': 'application/json'
                    }

                    response = requests.get(url, headers=headers)
                    print('response', response)
                    if response.status_code == 200:
                        data = response.json()
                        print(data)
                        if 'Emails' in data and data['Emails']:
                            print("EXISTTTTTTttt")
                            # print(data['Emails'])
                            for email in (data['Emails']):
                                print('email',email)
                                email_data = {}
                                email_data['zoho_mail'] = True
                                if email['time'] and email['time'] > '2022-01-01':
                                    if 'cc' in email and email['cc']:
                                        print('CC',email['cc'][0]['email'])
                                        email_data['email_cc'] = email['cc'][0]['email']
                                    if 'owner' in email and email['owner']:
                                        print('owner',email['owner'])
                                        user_zoho_id = 'zcrm_'+str(email['owner']['id'])
                                        print('user_zoho_id',user_zoho_id)
                                        user = self.env['res.users'].search([('zoho_record_reference','=',user_zoho_id)])
                                        print('user',user)
                                        if user:
                                            print('author',user.partner_id.id)
                                            email_data['author_id'] = user.partner_id.id
                                            print('55',self.env.user)
                                        else:
                                            print('NO AUTHOR')
                                            email_data['author_id'] = self.env.user.partner_id.id
                                            print('55', self.env.user)
                                    if 'subject' in email and email['subject']:
                                        email_data['subject'] = email['subject']
                                    if 'from' in email and email['from']:
                                        email_data['email_from'] = email['from']['email']
                                    if 'to' in email and email['to']:
                                        email_data['email_to'] = email['to'][0]['email']
                                    if 'status' in email and email['status']:
                                        print('status',email['status'][0]['type'])
                                        if email['status'][0]['type'] == 'Sent':
                                            email_data['state'] = 'sent'
                                        elif email['status'][0]['type'] == 'Opened':
                                            email_data['state'] = 'outgoing'
                                        else:
                                            email_data['state'] = 'received'
                                    # if 'time' in email and email['time']:
                                    #     # email_data['mail_sent_time'] = Datetime(email['time'])
                                    #     # print('TIME',email_data)
                                    #     print('TIME',email['time'])
                                    #     if email['time'] > '2022-01-01':
                                    #         print('BIGGER')
                                    if 'message_id' in email and email['message_id']:
                                        message_url = url+'/'+email['message_id']
                                        message_response = requests.get(message_url, headers=headers)
                                        if message_response.status_code == 200:
                                            print('message_response',message_response)
                                            message_data = message_response.json()
                                            if 'Emails' in message_data and message_data['Emails'] and  message_data['Emails'][0]['content']:
                                                print('message_data',message_data)
                                                print('message_data',message_data['Emails'][0]['content'])
                                                email_data['body_html'] = message_data['Emails'][0]['content']
                                    print('email_data',email_data)
                                    create_email = self.env['mail.mail'].create(email_data)
                                    print('create_email',create_email)
                            if 'info' in data and data['info'] and data['info']['next_index']:
                                print('ppppp')
                                next_page_index = data['info']['next_index']
                                print('next_page_index',next_page_index)
                                while next_page_index != False:
                                    print('NEXT PAGE INDEX EXIST')
                                    print('NEXT PAGE INDEX EXIST email data',email_data)
                                    email_data = {}
                                    email_data['zoho_mail'] = True
                                    new_url = url + f'?index={next_page_index}'
                                    print('url',new_url)
                                    next_page_response = requests.get(new_url, headers=headers)
                                    print('next_page_response', next_page_response)
                                    if next_page_response.status_code == 200:
                                        print('NEXT PAGE DATA')
                                        next_data = next_page_response.json()
                                        if 'Emails' in next_data and next_data['Emails']:
                                            for email in (next_data['Emails']):
                                                print('next page email', email)
                                                if email['time'] and email['time'] > '2022-01-01':
                                                    if 'cc' in email and email['cc']:
                                                        print('CC',email['cc'][0]['email'])
                                                        email_data['email_cc'] = email['cc'][0]['email']
                                                    if 'owner' in email and email['owner']:
                                                        print('owner', email['owner'])
                                                        user_zoho_id = 'zcrm_' + str(email['owner']['id'])
                                                        print('user_zoho_id',user_zoho_id)
                                                        user = self.env['res.users'].search([('zoho_record_reference','=',user_zoho_id)])
                                                        print('user', user)
                                                        if user:
                                                            print('author',user.partner_id.id)
                                                            email_data['author_id'] = user.partner_id.id
                                                            print('55', self.env.user)
                                                        else:
                                                            print('NO AUTHOR')
                                                            email_data['author_id'] = self.env.user.partner_id.id
                                                            print('55', self.env.user)
                                                    if 'subject' in email and email['subject']:
                                                        email_data['subject'] = email['subject']
                                                    if 'from' in email and email['from']:
                                                        email_data['email_from'] = email['from']['email']
                                                    if 'to' in email and email['to']:
                                                        email_data['email_to'] = email['to'][0]['email']
                                                    if 'status' in email and email['status']:
                                                        print('status',email['status'][0]['type'])
                                                        if email['status'][0]['type'] == 'sent':
                                                            email_data['state'] = 'sent'
                                                        elif email['status'][0]['type'] == 'opened':
                                                            email_data['state'] = 'outgoing'
                                                        else:
                                                            email_data['state'] = 'received'
                                                    # if 'time' in email and email['time']:
                                                    #     # email_data['mail_sent_time'] = Datetime(email['time'])
                                                    #     # print('TIME',email_data)
                                                    #     print('TIME',email['time'])
                                                    #     if email['time'] > '2022-01-01':
                                                    #         print('BIGGER')
                                                    if 'message_id' in email and email['message_id']:
                                                        message_url = url + '/' + email['message_id']
                                                        message_response = requests.get(message_url,headers=headers)
                                                        if message_response.status_code == 200:
                                                            print('message_response',message_response)
                                                            message_data = message_response.json()
                                                            if 'Emails' in message_data and message_data['Emails'] and message_data['Emails'][0]['content']:
                                                                print('message_data',message_data)
                                                                print('message_data',message_data['Emails'][0]['content'])
                                                                email_data['body_html'] = message_data['Emails'][0]['content']
                                                    print('email_data', email_data)
                                                    create_email = self.env[
                                                        'mail.mail'].create(email_data)
                                                    print('create_email', create_email)

                                            if 'info' in next_data and next_data['info'] and next_data['info']['next_index']:
                                                print('NEXT PAGE INFO')
                                                next_page_index = next_data['info']['next_index']
                                                print('next_page_index_new',next_page_index)
                                            else:
                                                next_page_index = False
                                        else:
                                            print('NO EMAIL CONTENT')
                                            next_page_index = False

                                    else:
                                        print('NO NEXT PAGE DATA')
                                        next_page_index = False

                    job.write({
                       'state':'confirm'
                    })
            except Exception as e:
                _logger.error(
                    'Some error has been occurred in the processing'
                    ' of function:action_sync_conversations')
                job.write({
                    'state': 'failed'
                })
    def action_reset_to_draft(self):
        self.write({
            'state': 'draft'
        })
