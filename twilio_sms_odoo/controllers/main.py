from twilio.twiml.messaging_response import MessagingResponse
import logging
from odoo import http
from odoo.http import request
from datetime import datetime, date, timedelta
import json
from odoo import SUPERUSER_ID


class TwilioController(http.Controller):

    @http.route(['/receive_sms'], type='http', auth='none', cors='*', csrf=False, save_session=False, methods=['POST'])
    def sms_reply(self, **post):
        """Receives incoming messages and processes them without sending a response."""
        # Extract parameters from the request
        params = request.params
        
        # Create an incoming SMS record
        incoming_sms = request.env['twilio.incoming.sms'].sudo().create(
            {'incoming_message_sid': params.get('MessageSid'), 'phone': params.get('From'), 'body': params.get('Body'),
             'received_date': datetime.now()})
             
        logging.info('%s---------params',params.get('From'))
        
        logging.info('%s---------incoming_sms',incoming_sms.phone)
             
        # Find the associated lead, if any
        lead = request.env['crm.lead'].sudo().search([('phone_sanitized', '=', incoming_sms.phone)], limit=1)
        
        contact = request.env['res.partner'].sudo().search([('phone', '=', incoming_sms.phone)], limit=1)
        
        logging.info('%s---------lead',lead)
        
        # Get guest user from the context
        guest = request.env['mail.guest']._get_guest_from_context()
        
        logging.info('%s---------guest',guest)
        
        # Get odoobot user ID
        odoobot_id = request.env.ref('base.partner_root')
        
        logging.info('%s---------odoobot_id',odoobot_id)
        
        # If lead exists, post incoming message as a comment
        if lead:
            logging.info('%s---------lead2',lead)
            lead.with_user(SUPERUSER_ID).sudo().message_post(
                body=params.get('Body'),
                subject='Incoming SMS sent by customer:',
                message_type='comment',  # type of message (comment, email, etc.)
                subtype_id=request.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),  # subtype of message
                author_id=odoobot_id.id,  # id of the message's author
                author_guest_id=guest.id,
            )
            
            # Update lead's last incoming message
            lead.write({'last_incoming_message':params.get('Body')})
            
            # Send email notification for incoming SMS
            mail_template = request.env.ref('twilio_sms_odoo.mail_incoming_sms')
            mail_template.with_user(SUPERUSER_ID).sudo().send_mail(lead.id, force_send=True)
            
        if contact:
            contact.with_user(SUPERUSER_ID).sudo().message_post(
                body=params.get('Body'),
                subject='Incoming SMS sent by customer:',
                message_type='comment',  # type of message (comment, email, etc.)
                subtype_id=request.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),  # subtype of message
                author_id=odoobot_id.id,  # id of the message's author
                author_guest_id=guest.id,
            )
            
            # Update lead's last incoming message
            #lead.write({'last_incoming_message':params.get('Body')})
            
            # Send email notification for incoming SMS
            mail_template = request.env.ref('twilio_sms_odoo.mail_incoming_sms_contact')
            mail_template.with_user(SUPERUSER_ID).sudo().send_mail(contact.id, force_send=True)

        # Create a log entry for the Twilio response
        log = request.env['twilio.response.log'].sudo().create({
        'api_response': params,
        'date': datetime.now()
        })
        
        # Return a JSON response indicating success
        return json.dumps({'status': 'The message is created successfully in Odoo.'})

