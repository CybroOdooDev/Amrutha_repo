from odoo import fields, models


class Mail(models.Model):
    _inherit = 'mail.mail'

    zoho_reference = fields.Char('Zoho Id',
                                 help='Reference id of email in Zoho')
    file_reference = fields.Char('File Id', help='Reference of file in zoho')
    bcc = fields.Char('Bcc', help='Email Bcc')
    bounce_reason = fields.Char('Bounce Reason', help='Bounce Reason')
    source = fields.Char('Source', help='Source of Email')
    sent_from = fields.Char("send from", help='Send from')
    mail_sent_time = fields.Datetime('Zoho Mail Time', help='Zoho Mail Time')
    zoho_mail = fields.Boolean('Is Zoho Mail', help='Check whether the email is created from Zoho')
