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
        job = self.env['zoho.queue'].sudo().search([('state', '=', 'draft')],
                                                   order='id asc', limit=1)
        if job:
            try:
                for partner in job.data:
                    partner_id = self.env['res.partner'].browse(partner)
                    zoho_id = partner_id.zoho_record_id.replace("zcrm_", "")
                    url = f"https://www.zohoapis.com/crm/v7/Contacts/{zoho_id}/Emails"
                    headers = {
                        'Authorization': f'Bearer {job.instance_id.access_token}',
                        'Content-Type': 'application/json'
                    }
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if 'Emails' in data and data['Emails']:
                            for email in (data['Emails']):
                                email_data = {}
                                email_data['zoho_mail'] = True
                                if email['time'] and email['time'] > '2022-01-01':
                                    if 'cc' in email and email['cc']:
                                        email_data['email_cc'] = email['cc'][0]['email']
                                    if 'owner' in email and email['owner']:
                                        user_zoho_id = 'zcrm_'+str(email['owner']['id'])
                                        user = self.env['res.users'].search([('zoho_record_reference','=',user_zoho_id)])
                                        if user:
                                            email_data['author_id'] = user.partner_id.id
                                        else:
                                            email_data['author_id'] = self.env.user.partner_id.id
                                    if 'subject' in email and email['subject']:
                                        email_data['subject'] = email['subject']
                                    if 'from' in email and email['from']:
                                        email_data['email_from'] = email['from']['email']
                                    if 'to' in email and email['to']:
                                        email_data['email_to'] = email['to'][0]['email']
                                    if 'status' in email and email['status']:
                                        if email['status'][0]['type'] == 'Sent':
                                            email_data['state'] = 'sent'
                                        elif email['status'][0]['type'] == 'Opened':
                                            email_data['state'] = 'outgoing'
                                        else:
                                            email_data['state'] = 'received'

                                    if 'message_id' in email and email['message_id']:
                                        message_url = url+'/'+email['message_id']
                                        message_response = requests.get(message_url, headers=headers)
                                        if message_response.status_code == 200:
                                            message_data = message_response.json()
                                            if 'Emails' in message_data and message_data['Emails'] and  message_data['Emails'][0]['content']:
                                                email_data['body_html'] = message_data['Emails'][0]['content']
                                    create_email = self.env['mail.mail'].create(email_data)
                            if 'info' in data and data['info'] and data['info']['next_index']:
                                next_page_index = data['info']['next_index']
                                while next_page_index != False:
                                    email_data = {}
                                    email_data['zoho_mail'] = True
                                    new_url = url + f'?index={next_page_index}'
                                    next_page_response = requests.get(new_url, headers=headers)
                                    if next_page_response.status_code == 200:
                                        next_data = next_page_response.json()
                                        if 'Emails' in next_data and next_data['Emails']:
                                            for email in (next_data['Emails']):
                                                if email['time'] and email['time'] > '2022-01-01':
                                                    if 'cc' in email and email['cc']:
                                                        email_data['email_cc'] = email['cc'][0]['email']
                                                    if 'owner' in email and email['owner']:
                                                        user_zoho_id = 'zcrm_' + str(email['owner']['id'])
                                                        user = self.env['res.users'].search([('zoho_record_reference','=',user_zoho_id)])
                                                        if user:
                                                            email_data['author_id'] = user.partner_id.id
                                                        else:
                                                            email_data['author_id'] = self.env.user.partner_id.id
                                                    if 'subject' in email and email['subject']:
                                                        email_data['subject'] = email['subject']
                                                    if 'from' in email and email['from']:
                                                        email_data['email_from'] = email['from']['email']
                                                    if 'to' in email and email['to']:
                                                        email_data['email_to'] = email['to'][0]['email']
                                                    if 'status' in email and email['status']:
                                                        if email['status'][0]['type'] == 'sent':
                                                            email_data['state'] = 'sent'
                                                        elif email['status'][0]['type'] == 'opened':
                                                            email_data['state'] = 'outgoing'
                                                        else:
                                                            email_data['state'] = 'received'

                                                    if 'message_id' in email and email['message_id']:
                                                        message_url = url + '/' + email['message_id']
                                                        message_response = requests.get(message_url,headers=headers)
                                                        if message_response.status_code == 200:
                                                            message_data = message_response.json()
                                                            if 'Emails' in message_data and message_data['Emails'] and message_data['Emails'][0]['content']:
                                                                email_data['body_html'] = message_data['Emails'][0]['content']
                                                    create_email = self.env[
                                                        'mail.mail'].create(email_data)

                                            if 'info' in next_data and next_data['info'] and next_data['info']['next_index']:
                                                next_page_index = next_data['info']['next_index']
                                            else:
                                                next_page_index = False
                                        else:
                                            next_page_index = False

                                    else:
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
