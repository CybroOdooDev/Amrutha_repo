# -*- coding: utf-8 -*-
from email.policy import default

from odoo import api,models, fields, Command
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
import json
import logging
import traceback
_logger = logging.getLogger(__name__)


class InvoiceQueue(models.Model):
    _name = 'invoice.queue'
    _description = 'Invoice Queue'

    name = fields.Char('Name', help='Name of Queue')
    action = fields.Char('Action', help='Action need to perform')
    data = fields.Json('Data', help='Content of Data')
    data_string = fields.Text('Lines in Batch', compute='_compute_data_string', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', help="state of Queue"
    )
    errors = fields.Char(string="Caused Error")
    detailed_error = fields.Char(string="Detailed Error")

    @api.depends('data')
    def _compute_data_string(self):
        for rec in self:
            try:
                rec.data_string = json.dumps(rec.data, indent=2)
            except Exception:
                rec.data_string = str(rec.data)

    def action_generate_recurring_bills(self):
        """ Taking the field 'data' which carries batches of 2000 rental order lines that to be invoiced and processing the functions """
        job = self.env['invoice.queue'].sudo().search([('state', '=', 'draft')],
                                                   order='id asc', limit=1)
        if job:
            _logger.info('Generating Recurring bills')
            try:
                main_prod = None
                today = fields.Date.today()
            # Group order lines by sale order
                orders_grouped = {}
                for line in job.data:
                    line_id = self.env['sale.order.line'].browse(line)
                    if not line_id.order_id.close_order:
                        if line_id.order_id not in orders_grouped:
                            orders_grouped[line_id.order_id] = []
                        orders_grouped[line_id.order_id].append(line_id)
            # Generate invoices for each sale order
                for sale_order, order_lines in orders_grouped.items():
                    section_prod = sale_order.get_sections_with_products()
                    invoice_vals = {
                        'ref': sale_order.client_order_ref or '',
                        'move_type': 'out_invoice',
                        'narration': sale_order.note,
                        'currency_id': sale_order.currency_id.id,
                        'campaign_id': sale_order.campaign_id.id,
                        'medium_id': sale_order.medium_id.id,
                        'source_id': sale_order.source_id.id,
                        'team_id': sale_order.team_id.id,
                        'partner_id': sale_order.partner_invoice_id.id,
                        'partner_shipping_id': sale_order.partner_shipping_id.id,
                        'fiscal_position_id': (
                                    sale_order.fiscal_position_id or sale_order.fiscal_position_id._get_fiscal_position(
                                sale_order.partner_invoice_id)).id,
                        'invoice_origin': sale_order.name,
                        'date': today,
                        'invoice_date': today,
                        'invoice_date_due': today if not sale_order.payment_term_id else False,
                        'invoice_payment_term_id': sale_order.payment_term_id.id if sale_order.payment_term_id else False,
                        'preferred_payment_method_line_id': False,
                        'invoice_user_id': sale_order.user_id.id,
                        'payment_reference': sale_order.reference,
                        'transaction_ids': [Command.set(sale_order.transaction_ids.ids)],
                        'company_id': sale_order.company_id.id,
                        'invoice_line_ids': [],
                        'user_id': sale_order.user_id.id,
                        'name': '/'
                    }
                    # Adding all the order lines to the invoice
                    for line in order_lines:
                        rental_start = line.rental_start_date
                        # Get all lines of the same rental_start_date in the same order
                        same_date_lines = sale_order.order_line.filtered(lambda l: l.rental_start_date == rental_start)
                        # Check if any main product line is not fully delivered
                        incomplete_main_product = any(
                            not l.product_id.charges_ok and l.product_uom_qty != l.qty_delivered for l in same_date_lines
                        )
                        for section, order_line in section_prod.items():
                            if line in order_line and line.qty_delivered:
                                if incomplete_main_product:
                                    continue
                                if line.is_sale and line.product_template_id.charges_ok == False:
                                    invoice_vals['invoice_line_ids'].append(Command.create(
                                        line._prepare_invoice_line(
                                            name=f"Sale",
                                            product_id=line.product_id.id,
                                            price_unit=line.price_unit,
                                            quantity=line.qty_delivered - line.qty_invoiced,
                                        )
                                    ))

                                if not line.is_sale and line.product_template_id.charges_ok == False:
                                    if sale_order.bill_terms == 'advance':
                                        invoice_vals['invoice_line_ids'].append(Command.create(
                                            line._prepare_invoice_line(
                                                name=f"Rental",
                                                product_id=line.product_id.id,
                                                price_unit=line.price_unit,
                                                quantity=line.qty_delivered - line.qty_returned,
                                            )
                                        ))
                                        main_prod = line.product_id.name
                                    if sale_order.bill_terms == 'late' and not sale_order.pricelist_id.product_pricing_ids:
                                        invoice_vals['invoice_line_ids'].append(Command.create(
                                            line._prepare_invoice_line(
                                                name=f"Rental",
                                                product_id=line.product_id.id,
                                                price_unit=line.price_unit,
                                                quantity=line.qty_delivered - line.qty_returned,
                                            )
                                        ))
                                        main_prod = line.product_id.name
                                    if sale_order.bill_terms == 'late' and sale_order.pricelist_id.product_pricing_ids:
                                        pricelist_template_ids = sale_order.pricelist_id.product_pricing_ids.mapped(
                                            'product_template_id')
                                        if line.product_template_id in pricelist_template_ids:
                                            for range in sale_order.pricelist_id.product_pricing_ids:
                                                if range.product_template_id == line.product_template_id:
                                                    # Check the rental period in the pricelist and recurring plan in the order
                                                    pricelist_period_duration = range.recurrence_id.duration
                                                    pricelist_period_unit = range.recurrence_id.unit
                                                    if (pricelist_period_duration == 1) and (pricelist_period_unit == 'day'):
                                                        if line['pickedup_lot_ids']:
                                                            for lot in line['pickedup_lot_ids']:
                                                                date_lines = self.env['product.return.dates'].search([
                                                                    ('order_id', '=', sale_order.id),
                                                                    ('serial_number', '=', lot.id),
                                                                ])
                                                                if date_lines and date_lines.return_date:
                                                                    date_lines.invoice_count += 1
                                                                if date_lines.invoice_count <= 1:
                                                                    invoice_vals['invoice_line_ids'].append(Command.create(
                                                                        line._prepare_invoice_line(
                                                                            name=f"Rental with Per Day Charge - {lot.name}",
                                                                            product_id=date_lines.product_id.id,
                                                                            price_unit=date_lines.total_price,
                                                                            quantity=1,
                                                                        )
                                                                    ))
                                                        main_prod = line.product_id.name
                                                    else:
                                                        invoice_vals['invoice_line_ids'].append(Command.create(
                                                            line._prepare_invoice_line(
                                                                name=f"Rental",
                                                                product_id=line.product_id.id,
                                                                price_unit=line.price_unit,
                                                                quantity=line.qty_delivered - line.qty_returned,
                                                            )
                                                        ))
                                                        main_prod = line.product_id.name
                                        else:
                                            invoice_vals['invoice_line_ids'].append(Command.create(
                                                line._prepare_invoice_line(
                                                    name=f"Rental",
                                                    product_id=line.product_id.id,
                                                    price_unit=line.price_unit,
                                                    quantity=line.qty_delivered - line.qty_returned,
                                                )
                                            ))
                                            main_prod = line.product_id.name

                                if not line.is_sale and line.product_template_id.charges_ok == True:
                                    invoice_vals['invoice_line_ids'].append(Command.create(
                                        line._prepare_invoice_line(
                                            name=f"Rental Service Charges for {main_prod}",
                                            product_id=line.product_id.id,
                                            price_unit=line.price_unit,
                                            quantity=line.qty_delivered - line.qty_returned,
                                        )))

                    # Removing lines with zero qty and zero price from the invoice
                    invoice_vals['invoice_line_ids'] = [
                        vals for vals in invoice_vals['invoice_line_ids']
                        if vals[2].get('quantity', 0.0) != 0.0 and vals[2].get('price_unit', 0.0) != 0.0
                    ]
                    invoice = self.env['account.move'].create(invoice_vals)
                    if invoice and not sale_order.has_returnable_lines:
                        sale_order.close_order = True

                    # Updating the Next bill date
                    if invoice:
                        sale_order = invoice.line_ids.sale_line_ids.order_id
                        for lines in invoice.line_ids.sale_line_ids:
                            if  not lines.product_template_id.charges_ok:
                                if lines.qty_delivered >= line.qty_returned:
                                    lines.invoice_status = 'to invoice'
                                start_date = lines.next_bill_date

                                billing_period_unit = sale_order.recurring_plan_id.billing_period_unit
                                billing_period_value = sale_order.recurring_plan_id.billing_period_value

                                if billing_period_unit == "day":
                                    lines.next_bill_date = date_utils.add(start_date, days=billing_period_value)
                                elif billing_period_unit == "month":
                                    lines.next_bill_date = date_utils.add(start_date, months=billing_period_value)
                                elif billing_period_unit == "year":
                                    lines.next_bill_date = date_utils.add(start_date, years=billing_period_value)
                                else:
                                    raise ValueError(f"Unsupported billing_period_unit: {billing_period_unit}")

                job.write({'state': 'completed'})

            except Exception as e:
                tb = traceback.format_exc()
                _logger.error(f"Error while generating recurring bills: {tb}")
                job.write({
                    'state': 'failed',
                    'errors': e,
                    'detailed_error': f"{tb} \nRental Order: {str(sale_order)} \nOrder Lines: {line}",
                })