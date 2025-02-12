# -*- coding: utf-8 -*-
from importlib.metadata import requires
from google.auth import default
from odoo import api, models, fields, _, Command
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
from bs4 import BeautifulSoup
from odoo import models, fields


class ProductReturnDates(models.Model):
    _name = 'product.return.dates'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    # product_id = fields.Many2one('product.product', required=True)
    product_id = fields.Many2one('product.product')
    serial_number = fields.Many2one('stock.lot', domain="[('product_id', '=', product_id)]")
    warehouse_id = fields.Many2one('stock.warehouse')
    quantity = fields.Integer(default=1)
    per_day_charges = fields.Float('Per Day Charge')
    total_days = fields.Integer('Total Days', compute='_compute_total_days_price', )
    total_price = fields.Float('Total Price', compute='_compute_total_days_price', )
    delivery_date = fields.Date('Delivery Date')
    return_date = fields.Date('Return Date')
    delivery_driver = fields.Many2one('res.partner')
    pickup_driver = fields.Many2one('res.partner')
    invoice_count = fields.Integer(string="Invoice Count", default=0)
    signature_status = fields.Selection(selection=[('initial', "Initial"),
                                                   ('delivery', "Delivery Sent"),
                                                   ('pickup', "Pick-Up Sent"),
                                                   ],
                                        string="Signature Status",
                                        default="initial",
                                        store=True)

    @api.depends('delivery_date', 'return_date', 'total_days')
    def _compute_total_days_price(self):
        """ To compute total days of rental """
        for record in self:
            today = fields.Date.from_string(fields.date.today())
            delivery = fields.Date.from_string(record.delivery_date)
            record.quantity = 1
            if record.delivery_date and record.return_date:
                end = fields.Date.from_string(record.return_date)
                record.total_days = (end - delivery).days
            if record.delivery_date and not record.return_date:
                record.total_days = (today - delivery).days

            record.total_price = record.quantity * record.total_days * record.per_day_charges

    def action_send_delivery_signature(self):
        """ Button action for sending Delivery signature request to the driver """
        if (self.signature_status == 'initial'):
            if self.delivery_driver:
                self.signature_status = 'delivery'
            else:
                raise ValidationError("Select a Delivery Driver")
        # Taking the notes added inside the Internal Notes field and passing to the template
        html_content = self.order_id.description
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            plain_text = soup.get_text(separator=" ", strip=True)
        else:
            plain_text = ""
        pdf_report = self.env.ref('rental_customization.action_delivery_pdf_slip')

        data = {
            'ticket_no': self.order_id.name,
            'logo': self.order_id.company_id.logo,
            'customer': self.order_id.partner_id.name,
            'notes': plain_text,
            'location':self.warehouse_id
        }
        content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
            pdf_report.report_name,
            res_ids=self.ids,
            data=data,
        )
        attatchment = self.env['ir.attachment'].create([{
            'name': 'delivery_slip',
            'type': 'binary',
            'datas': base64.b64encode(content).decode('utf-8'),
            'store_fname': 'delivery_slip',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        }])

        sign_template = self.env['sign.template'].create([{
            'attachment_id': attatchment.id,
            'sign_item_ids': [fields.Command.create({
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                'responsible_id': self.env.ref('sign.sign_item_role_customer').id,
                'page': 1,
                'posX': 0.283,
                'posY': 0.681,
                'width': 0.2,
                'height': 0.05,
            })],
        }])

        request = self.env['sign.request'].sudo().create([{
            'template_id': sign_template.id,
            'request_item_ids': [fields.Command.create({
                'partner_id': self.delivery_driver.id,
                'role_id': 1,
                'mail_sent_order': 1})],
            'reference': f"delivery_slip-{self.serial_number.name}",
            'subject': f'Signature Request - delivery_slip-{self.serial_number.name}',
            'message': False, 'message_cc': False,
            'validity': fields.Datetime.today(),
            'reminder': 7,
            'reminder_enabled': False,
            'reference_doc': f"sale.order,{self.order_id.id}"}])

        if request.reference_doc:
            model = request.reference_doc  and self.env['ir.model']._get(request._name)
            if model.is_mail_thread:
                body = _("A signature request has been linked to this document: %s", request._get_html_link())
                self.order_id.message_post(body=body)
                body = _("%s has been linked to this sign request.",  self.order_id._get_html_link())
                request.message_post(body=body)

    def action_send_pickup_signature(self):
        """ Button action for sending Pick-Up signature request to the driver """
        if self.signature_status == 'delivery':
            if not self.pickup_driver:
                raise ValidationError("Select a Pick-Up Driver")
            if not self.return_date:
                raise ValidationError("Fill the Return Date")
            if self.pickup_driver and self.return_date:
                self.signature_status = 'pickup'

        # Taking the notes added inside the Internal Notes field and passing to the template
        html_content = self.order_id.description
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            plain_text = soup.get_text(separator=" ", strip=True)
        else:
            plain_text = ""

        pdf_report = self.env.ref('rental_customization.action_pickup_pdf_slip')
        stock_quant = self.env['stock.lot'].search(
            [('name', '=', self.serial_number.name), ('product_id', '=', self.product_id.id)])
        if stock_quant:
            location = stock_quant.location_id.warehouse_id
        else:
            location = ""
        data = {
            'ticket_no': self.order_id.name,
            'logo': self.order_id.company_id.logo,
            'customer': self.order_id.partner_id.name,
            'notes': plain_text ,
            'location':location
        }
        content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
            pdf_report.report_name,
            res_ids=self.ids,
            data=data,
        )
        attatchment = self.env['ir.attachment'].create([{
            'name': 'pickup_slip',
            'type': 'binary',
            'datas': base64.b64encode(content).decode('utf-8'),
            'store_fname': 'pickup_slip',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        }])
        sign_template = self.env['sign.template'].create([{
            'attachment_id': attatchment.id,
            'sign_item_ids': [fields.Command.create({
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                'responsible_id': self.env.ref('sign.sign_item_role_customer').id,
                'page': 1,
                'posX': 0.283,
                'posY': 0.681,
                'width': 0.2,
                'height': 0.05,
            })],
        }])

        request = self.env['sign.request'].sudo().create([{
            'template_id': sign_template.id,
            'request_item_ids': [fields.Command.create({
                'partner_id': self.pickup_driver.id,
                'role_id': 1,
                'mail_sent_order': 1})],
            'reference': f"pickup_slip-{self.serial_number.name}",
            'subject': f'Signature Request - pickup_slip-{self.serial_number.name}',
            'message': False, 'message_cc': False,
            'validity': fields.Datetime.today(),
            'reminder': 7,
            'reminder_enabled': False,
            'reference_doc': f"sale.order,{self.order_id.id}"}])
        if request.reference_doc:
            model = request.reference_doc and self.env['ir.model']._get(request._name)
            if model.is_mail_thread:
                body = _("A signature request has been linked to this document: %s", request._get_html_link())
                self.order_id.message_post(body=body)
                body = _("%s has been linked to this sign request.", self.order_id._get_html_link())
                request.message_post(body=body)

    def action_signature_msg(self):
        """ Button action for showing validation message """
        if self.signature_status == 'pickup':
            raise ValidationError("Signature requests are already Sent")
