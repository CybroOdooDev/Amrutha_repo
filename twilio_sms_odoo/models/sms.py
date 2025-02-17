from odoo import api, Command, fields, models, tools, _
from odoo import SUPERUSER_ID
import os
from twilio.rest import Client
import logging
import threading
from odoo.addons.phone_validation.tools import phone_validation
from odoo.tools import html2plaintext, plaintext2html

_logger = logging.getLogger(__name__)

class CRMLead(models.Model):
    _inherit = "crm.lead"
    
    last_incoming_message = fields.Char(string='Last Incoming Message')

    def send_incoming_sms_email(self, lead, body):
        # Search for the CRM lead record with the given ID
        crm = self.env['crm.lead'].search([('id', '=', lead.id)])
        
        # Loop through each CRM lead record
        for rec in crm:
        
            # Compose the email body with dynamic placeholders
            message_body = """
                <div>
                <br/>
                    Hi {salesperson}, {partner_name} has replied back ! <br/>
                    <br/>
                    {body}
                    <br/>
                    <br/>To view the customer profile or lead, click the button below.
                 
                    <div style="margin: 16px 0; text-align: center;">
                        <a href="/web#id={partner_id}&amp;model=res.partner&amp;view_type=form"
                           style="text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px; padding: 10px; display: inline-block; margin-right: 10px;">
                            <strong>View Contact</strong>
                        </a>
                        <a href="/web#id={lead}&amp;model=crm.lead&amp;view_type=form"
                           style="text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px; padding: 10px; display: inline-block; margin-right: 10px;">
                            <strong>View Lead</strong>
                        </a>
                    </div>
                </div>
            """.format(salesperson = rec.user_id.name, partner_name=rec.partner_id.name or 'user', partner_id=rec.partner_id.id, lead=rec.id, body=body)
        # Loop through each CRM lead record again
        for rec in crm:
        
            # Create a mail composer for sending email
            composer = self.env['mail.compose.message'].with_user(SUPERUSER_ID).with_context(
                mail_notify_author=self.user_id.login,
                default_composition_mode='comment',
                default_model='crm.lead',
                default_res_ids=rec.ids,
                default_template_id=self.env.ref('twilio_sms_odoo.mail_incoming_sms').id,
                default_email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                default_record_name=rec.name,
                default_partner_ids = [self.user_id.partner_id.id],
            ).create({
                'message_type': 'comment',
                'body': message_body,
            })
            
            # Send the email
            composer._action_send_mail()

class ResConfigSettings(models.TransientModel):

      _inherit = 'res.config.settings'
      
      twilio_account_sid = fields.Char(string='Twilio Account SID')
      twilio_auth_token = fields.Char(string='Twilio Auth Token',config_parameter='twilio_sms_odoo.twilio_auth_token')
      twilio_phone = fields.Char(string='Twilio Phone',config_parameter='twilio_sms_odoo.twilio_phone')

class TwilioOutgoingSMS(models.TransientModel):

      _inherit = 'mailing.sms.test'
     
      def action_send_twilio_outgoing_sms(self):
      
          # Ensure only one record is processed
          self.ensure_one()
          
          # Retrieve Twilio account credentials and phone number from configuration parameters
          account_sid = self.env['ir.config_parameter'].sudo().get_param('mail.twilio_account_sid')
          auth_token = self.env['ir.config_parameter'].sudo().get_param('twilio_sms_odoo.twilio_auth_token')
          phone = self.env['ir.config_parameter'].sudo().get_param('twilio_sms_odoo.twilio_phone')

          # Initialize Twilio client          
          client = Client(account_sid, auth_token)
          
          # Split numbers into a list and sanitize them
          numbers = [number.strip() for number in self.numbers.splitlines()]
          sanitized_numbers = [self.env.user._phone_format(number=number) for number in numbers]
          
          # Filter out invalid numbers
          invalid_numbers = [number for sanitized, number in zip(sanitized_numbers, numbers) if not sanitized]
           
          # Retrieve the record associated with the mailing 
          record = self.env[self.mailing_id.mailing_model_real].search([], limit=1)
          
          # Extract plaintext body from mailing          
          body = self.mailing_id.body_plaintext
          if record:
          
              # Render template with record data
              body = self.env['mail.render.mixin']._render_template(body, self.mailing_id.mailing_model_real, record.ids)[record.id]
          
          # Create outgoing SMS messages
          new_sms_messages_sudo = self.env['sms.sms'].sudo().create([{'body': body, 'number': number} for number in sanitized_numbers])
          
          # Send SMS messages via Twilio
          for message_sms in new_sms_messages_sudo:

              message = client.messages.create(
                     body= message_sms.body,
                     from_= phone,
                     to=message_sms.number
                     )
                     
              # Fetch message details
              message_id = client.messages(message.sid).fetch()
              
              # Create outgoing log entry
              outgoing_log = self.env['twilio.outgoing.log'].sudo().create({'api_response':message_id,'status':message_id.status,'message_id':message_id.sid,'to_phone':message_id.to,'body':message_id.body})
          
class TwilioOutgoingLog(models.Model):
   _name = 'twilio.outgoing.log'
   _order = 'id desc'
   
   api_response = fields.Char(string='API Response')
   status = fields.Char(string='Status')
   message_id = fields.Char(string='Message SID')
   to_phone = fields.Char(string='To Phone')
   body = fields.Char(string='Body')
   

class TwilioResponseLog(models.Model):
   _name = 'twilio.response.log'
   _order = 'id desc'
   
   api_response = fields.Char(string='API Response')
   date = fields.Datetime(string='Date')
   
class SMS(models.Model):

   _inherit = 'sms.sms'
   
   def send_twilio_sms(self, auto_commit=False):
        """
        Main API method to send SMS.   
        :param auto_commit: Whether to commit after each batch of SMS.
        """
        
        # Filter SMS records that are outgoing and not flagged for deletion
        self = self.filtered(lambda sms: sms.state == 'outgoing' and not sms.to_delete)
        
        # Split SMS records into batches
        for batch_ids in self._split_batch():
        
            # Send SMS for each batch
            self.browse(batch_ids)._send_twilio_sms()
            
            # Auto-commit if requested, except in testing mode
            if auto_commit is True and not getattr(threading.current_thread(), 'testing', False):
                self._cr.commit()
   
   @api.model
   def _process_queue(self, ids=None):
        """ Send immediately queued messages, committing after each message is sent.
        This is not transactional and should not be called during another transaction!

       :param list ids: optional list of emails ids to send. If passed no search
         is performed, and these ids are used instead.
        """
        domain = [('state', '=', 'outgoing'), ('to_delete', '!=', True)]

        filtered_ids = self.search(domain, limit=10000).ids  # TDE note: arbitrary limit we might have to update
        if ids:
            ids = list(set(filtered_ids) & set(ids))
        else:
            ids = filtered_ids
        ids.sort()

        res = None
        try:
            # auto-commit except in testing mode
            auto_commit = not getattr(threading.current_thread(), 'testing', False)
            res = self.browse(ids).send_twilio_sms(auto_commit=auto_commit)
        except Exception:
            _logger.exception("Failed processing SMS queue")
        return res
   
   def _send_twilio_sms(self):
       """
       Method to send SMS messages via Twilio.
       """
       # Retrieve Twilio account credentials and phone number from configuration parameters
       account_sid = self.env['ir.config_parameter'].sudo().get_param('mail.twilio_account_sid')
       auth_token = self.env['ir.config_parameter'].sudo().get_param('twilio_sms_odoo.twilio_auth_token')
       phone = self.env['ir.config_parameter'].sudo().get_param('twilio_sms_odoo.twilio_phone') 
       
       # Initialize Twilio client
       client = Client(account_sid, auth_token)
       
       # Group SMS records by message body
       messages = [{
            'content': body,
            'numbers': [{'number': sms.number, 'uuid': sms.uuid} for sms in body_sms_records],
        } for body, body_sms_records in self.grouped('body').items()]
        
       # Send messages
       for message in messages:
           try:
              # Send message via Twilio
              message_sent = client.messages.create(
                     body= message['content'],
                     from_= phone,
                     to=message['numbers'][0]['number'],
                     )
                     
              # Fetch message details
              message_id = client.messages(message_sent.sid).fetch()
              
              # Update SMS records and create outgoing log entry
              sms = self.env['sms.sms'].sudo().search([('uuid','=',message['numbers'][0]['uuid'])])
              outgoing_log = self.env['twilio.outgoing.log'].sudo().create({'api_response':message_id,'status':message_id.status,'message_id':message_id.sid,'to_phone':message_id.to,'body':message_id.body})
              sms.write({'state':'sent','to_delete':True})
           except:
           
              # Handle exceptions (e.g., mobile number not verified)
              sms = self.env['sms.sms'].sudo().search([('uuid','=',message['numbers'][0]['uuid'])])
              sms.write({'state':'canceled'})           
       return True

class TwilioIncomingSMS(models.Model):

   _name = 'twilio.incoming.sms'
   
   incoming_message_sid = fields.Char(string='Incoming Message SID')
   phone = fields.Char(string='From',unaccent=False)
   body = fields.Text(string='Body')
   received_date = fields.Datetime(string='Date')
   formatted_phone = fields.Char(string='Formatted Phone',compute='_compute_formatted_phone')
   
   @api.depends('phone')
   def _compute_formatted_phone(self):
       """
       Compute method to format the phone number.
       """
       for record in self:
       
           # Check if the phone number is not empty
           if record.phone:
           
              # Format the phone number
              phone_number_formatted = record._phone_format(fname='phone',force_format='INTERNATIONAL') or record.phone
              
              # Assign the formatted phone number to the 'formatted_phone' field
              record.formatted_phone = phone_number_formatted
           else:
           
              # If the phone number is empty, set 'formatted_phone' to None
              record.formatted_phone = None

class MailThread(models.AbstractModel):

      _inherit = 'mail.thread'
      
      def _notify_thread_by_sms(self, message, recipients_data, msg_vals=False,
                              sms_numbers=None, sms_pid_to_number=None,
                              resend_existing=False, put_in_queue=False, **kwargs):
        """ Notification method: by SMS.

        :param message: ``mail.message`` record to notify;
        :param recipients_data: list of recipients information (based on res.partner
          records), formatted like
            [{'active': partner.active;
              'id': id of the res.partner being recipient to notify;
              'groups': res.group IDs if linked to a user;
              'notif': 'inbox', 'email', 'sms' (SMS App);
              'share': partner.partner_share;
              'type': 'customer', 'portal', 'user;'
             }, {...}].
          See ``MailThread._notify_get_recipients``;
        :param msg_vals: dictionary of values used to create the message. If given it
          may be used to access values related to ``message`` without accessing it
          directly. It lessens query count in some optimized use cases by avoiding
          access message content in db;

        :param sms_numbers: additional numbers to notify in addition to partners
          and classic recipients;
        :param pid_to_number: force a number to notify for a given partner ID
              instead of taking its mobile / phone number;
        :param resend_existing: check for existing notifications to update based on
          mailed recipient, otherwise create new notifications;
        :param put_in_queue: use cron to send queued SMS instead of sending them
          directly;
        """
        sms_pid_to_number = sms_pid_to_number if sms_pid_to_number is not None else {}
        sms_numbers = sms_numbers if sms_numbers is not None else []
        sms_create_vals = []
        sms_all = self.env['sms.sms'].sudo()

        # pre-compute SMS data
        body = msg_vals['body'] if msg_vals and 'body' in msg_vals else message.body
        sms_base_vals = {
            'body': html2plaintext(body),
            'mail_message_id': message.id,
            'state': 'outgoing',
        }

        # notify from computed recipients_data (followers, specific recipients)
        partners_data = [r for r in recipients_data if r['notif'] == 'sms']
        partner_ids = [r['id'] for r in partners_data]
        if partner_ids:
            for partner in self.env['res.partner'].sudo().browse(partner_ids):
                number = sms_pid_to_number.get(partner.id) or partner.mobile or partner.phone
                sms_create_vals.append(dict(
                    sms_base_vals,
                    partner_id=partner.id,
                    number=partner._phone_format(number=number) or number,
                ))

        # notify from additional numbers
        if sms_numbers:
            tocreate_numbers = [
                self._phone_format(number=sms_number) or sms_number
                for sms_number in sms_numbers
            ]
            sms_create_vals += [dict(
                sms_base_vals,
                partner_id=False,
                number=n,
                state='outgoing' if n else 'error',
                failure_type='' if n else 'sms_number_missing',
            ) for n in tocreate_numbers]

        # create sms and notification
        existing_pids, existing_numbers = [], []
        if sms_create_vals:
            sms_all |= self.env['sms.sms'].sudo().create(sms_create_vals)

            if resend_existing:
                existing = self.env['mail.notification'].sudo().search([
                    '|', ('res_partner_id', 'in', partner_ids),
                    '&', ('res_partner_id', '=', False), ('sms_number', 'in', sms_numbers),
                    ('notification_type', '=', 'sms'),
                    ('mail_message_id', '=', message.id)
                ])
                for n in existing:
                    if n.res_partner_id.id in partner_ids and n.mail_message_id == message:
                        existing_pids.append(n.res_partner_id.id)
                    if not n.res_partner_id and n.sms_number in sms_numbers and n.mail_message_id == message:
                        existing_numbers.append(n.sms_number)

            notif_create_values = [{
                'author_id': message.author_id.id,
                'mail_message_id': message.id,
                'res_partner_id': sms.partner_id.id,
                'sms_number': sms.number,
                'notification_type': 'sms',
                'sms_id_int': sms.id,
                'sms_tracker_ids': [Command.create({'sms_uuid': sms.uuid})] if sms.state == 'outgoing' else False,
                'is_read': True,  # discard Inbox notification
                'notification_status': 'ready' if sms.state == 'outgoing' else 'exception',
                'failure_type': '' if sms.state == 'outgoing' else sms.failure_type,
            } for sms in sms_all if (sms.partner_id and sms.partner_id.id not in existing_pids) or (not sms.partner_id and sms.number not in existing_numbers)]
            if notif_create_values:
                self.env['mail.notification'].sudo().create(notif_create_values)

            if existing_pids or existing_numbers:
                for sms in sms_all:
                    notif = next((n for n in existing if
                                 (n.res_partner_id.id in existing_pids and n.res_partner_id.id == sms.partner_id.id) or
                                 (not n.res_partner_id and n.sms_number in existing_numbers and n.sms_number == sms.number)), False)
                    if notif:
                        notif.write({
                            'notification_type': 'sms',
                            'notification_status': 'ready',
                            'sms_id_int': sms.id,
                            'sms_tracker_ids': [Command.create({'sms_uuid': sms.uuid})],
                            'sms_number': sms.number,
                        })

        if sms_all and not put_in_queue:
            sms_all.filtered(lambda sms: sms.state == 'outgoing')._send_twilio_sms()

        return True
        
class SMSComposer(models.TransientModel):

      _inherit = 'sms.composer'
      
      def _action_send_sms_numbers(self):
        """
        Send SMS to multiple numbers.
        """
        
        # Prepare SMS values for each number
        sms_values = [{'body': self.body, 'number': number} for number in self.sanitized_numbers.split(',')]
        
        # Create SMS records with prepared values and send them via Twilio
        self.env['sms.sms'].sudo().create(sms_values)._send_twilio_sms()
        return True
