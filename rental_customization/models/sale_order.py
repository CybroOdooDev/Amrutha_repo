# -*- coding: utf-8 -*-
from importlib.metadata import requires
from re import search

from google.auth import default
from odoo import api,models, fields, Command
import pytz
from odoo.tools import date_utils
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """To add new fields in the rental order"""
    _inherit = "sale.order"

    recurring_plan_id = fields.Many2one("rental.recurring.plan",string="Rental Recurring Plan",
                                        default=lambda self: self._get_default_recurring_plan())
    bill_terms = fields.Selection(selection=[('advance', "Advance Bill"),('late', "Late Bill")],
                                  string="Bill Terms",default='late')
    show_update_button = fields.Boolean(string="Show Update Button", default=False, store=True)
    header_start_date = fields.Datetime(help="Header level start date for lines")
    header_return_date = fields.Datetime(help="Header level end date for lines")
    date_records_line = fields.One2many(
        comodel_name='product.return.dates',
        inverse_name='order_id',
        string="Date Records Lines",
        copy=True, auto_join=True)

    def _get_default_recurring_plan(self):
        """Get the default recurring plan (e.g., monthly)."""
        default_plan = self.env['rental.recurring.plan'].search([('is_default','=','True')])
        return default_plan.id if default_plan else False

    @api.onchange('bill_terms')
    def _onchange_bill_terms(self):
        if self.state == 'sale':
            raise ValidationError("Can't change Bill Terms after Order Confirmation")
        for lines in self.order_line:
                if self.bill_terms == "advance" and not lines.product_template_id.charges_ok:
                    lines.price_unit = lines.product_template_id.list_price
                if self.bill_terms == 'late' and lines.product_template_id.is_per_day_charge and not lines.product_template_id.charges_ok:
                    lines.price_unit = lines.product_template_id.per_day_charge

    @api.onchange('rental_start_date', 'rental_return_date')
    def _onchange_rental_dates(self):
        """Show the button if rental dates change."""
        self.show_update_button = True

    def update_dates(self):
        """ 'Update Button' action - To apply changes in header level start date to the line level dates"""
        self.header_start_date = self.rental_start_date
        self.header_return_date = self.rental_return_date

        for order_line in self.order_line:
            if self.header_start_date and self.header_return_date :
                    order_line.rental_start_date = self.header_start_date.astimezone(pytz.utc).replace(tzinfo=None)
                    if not order_line.is_sale:
                        order_line.rental_end_date = self.header_return_date.astimezone(pytz.utc).replace(tzinfo=None)
                    self.show_update_button = False
            if not self.header_start_date and self.header_return_date:
                raise ValueError("Start Date and End Date must be set on the order before updating lines.")

    @api.onchange('order_line')
    def _onchange_order_line(self):
        """ changing the invoice policy of a product as they are added to a Rental order """
        if self.is_rental_order:
            for line in self.order_line:
                if line.product_template_id:
                    line.product_template_id.invoice_policy = "delivery"

            # Ensuring one product within a section
            for line in self.order_line:
                if not line.display_type and not line.product_template_id.charges_ok:
                    current_sequence = line.sequence
                    section_above = any(
                        ol.sequence == current_sequence-1 and ol.display_type == 'line_section'
                        for ol in self.order_line
                    )

                    if not section_above:
                        raise ValidationError("Ensure each product is in a section and only one product per section.")

    def get_sections_with_products(self):
        """ Returns a dictionary with sections as keys and their products as values """
        section_products = {}
        current_section = None

        for line in self.order_line.sorted(key=lambda l: l.sequence):
            if line.display_type == 'line_section':

                # If the line is a section, set it as the current section
                current_section = line.name
                section_products[current_section] = []
            elif not line.display_type:
                # If the line is a product and there is a current section, add it
                if current_section:
                    section_products[current_section].append(line)
                else:
                    # If no section, add it to a generic 'No Section' key
                    section_products.setdefault('No Section', []).append(line)
        return section_products

    def _action_confirm(self):
        """ For creating sale order if is_sale boolean is enabled """
        for line in self.order_line:
            if line.is_sale:
                line.is_rental = False
            if line.product_template_id.charges_ok and not line.price_unit:
                raise ValidationError("Add unit Price for Service Charges if applicable;otherwise remove the line.")
        self.order_line._action_launch_stock_rule()
        return super(SaleOrder, self)._action_confirm()

    def action_add_sale_order(self):
        """ Adding sale order inside Rental order line """
        for line in self.order_line:
            if line.is_sale:
                line.is_rental = False
        self.order_line._action_launch_stock_rule()
        return super(SaleOrder, self)._action_confirm()

    def action_open_pickup(self):
        """ Pick-Up button validation """
        for line in self.order_line:
            if not line.is_sale and not line.next_bill_date:
                raise ValidationError("Rental Start Date and Next Bill Date is mandatory before Delivery And Return")

        return super().action_open_pickup()

    def generate_recurring_bills(self):
        """Continuous Bill creation based on the selected Rental recurring plan"""
        today = fields.Date.today()
        main_prod = None
        lines_to_invoice = self.env['sale.order.line'].search([])

        filtered_order_lines = lines_to_invoice.filtered(
            lambda line: (line.next_bill_date and line.next_bill_date.date() <= today) or line.is_sale
        )

        # Group order lines by sale order
        orders_grouped = {}
        for line in filtered_order_lines:
            if line.order_id not in orders_grouped:
                orders_grouped[line.order_id] = []
            orders_grouped[line.order_id].append(line)

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
                'invoice_date': today,
                'invoice_payment_term_id': sale_order.payment_term_id.id,
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
                for section, order_line in section_prod.items():
                    if line in order_line  and line.qty_delivered:
                        if line.is_sale and line.product_template_id.charges_ok== False :
                            invoice_vals['invoice_line_ids'].append(Command.create(
                                line._prepare_invoice_line(
                                    # name=f"Sale for {line.product_id.name}",
                                    name=f"Sale",
                                    product_id=line.product_id.id,
                                    price_unit=line.price_unit,
                                    quantity=line.qty_delivered - line.qty_invoiced,
                                )
                            ))

                        if not line.is_sale and line.product_template_id.charges_ok == False:
                            if sale_order.bill_terms == 'advance'or not line.product_template_id.is_per_day_charge:
                                invoice_vals['invoice_line_ids'].append(Command.create(
                                    line._prepare_invoice_line(
                                        # name=f"Rental for {line.product_id.name}",
                                        name=f"Rental",
                                        product_id=line.product_id.id,
                                        price_unit=line.price_unit,
                                        quantity=line.qty_delivered - line.qty_returned,
                                    )
                                ))
                                main_prod = line.product_id.name
                            if sale_order.bill_terms == 'late' and line.product_template_id.is_per_day_charge:
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
                                                    # name=f"Rental for {line.product_id.name}",
                                                    name=f"Rental with Per Day Charge - {lot.name}",
                                                    product_id=date_lines.product_id.id,
                                                    price_unit=date_lines.total_price,
                                                    quantity=1,
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
                                )
                            ))

                        if line.product_template_id.name == "Rental Delivery" or line.product_template_id.name == "Rental Pick-Up":
                            line.qty_delivered = 0

            # Removing lines with zero qty and zero price from the invoice
            invoice_vals['invoice_line_ids'] = [
                vals for vals in invoice_vals['invoice_line_ids']
                if vals[2].get('quantity', 0.0) != 0.0 and vals[2].get('price_unit', 0.0) != 0.0
            ]
            invoice = self.env['account.move'].create(invoice_vals)
        # Updating the Next bill date
            if invoice:
                sale_order = invoice.line_ids.sale_line_ids.order_id
                for lines in invoice.line_ids.sale_line_ids:
                    if not lines.product_template_id.charges_ok:
                        start_date = lines.next_bill_date

                        billing_period_unit = sale_order.recurring_plan_id.billing_period_unit
                        billing_period_value = sale_order.recurring_plan_id.billing_period_value

                        if billing_period_unit == "days":
                            lines.next_bill_date = date_utils.add(start_date, days=billing_period_value)
                        elif billing_period_unit == "month":
                            lines.next_bill_date = date_utils.add(start_date, months=billing_period_value)
                        elif billing_period_unit == "year":
                            lines.next_bill_date = date_utils.add(start_date, years=billing_period_value)
                        else:
                            raise ValueError(f"Unsupported billing_period_unit: {billing_period_unit}")
