# -*- coding: utf-8 -*-
from ast import literal_eval
from email.policy import default
from itertools import product
from time import process_time
from venv import create
from datetime import datetime
from odoo import api, fields, models, _
import pytz
from odoo.tools import date_utils
from odoo.exceptions import ValidationError
from odoo.fields import Command
import base64
from bs4 import BeautifulSoup

from odoo.tools.view_validation import READONLY


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    rental_start_date = fields.Date(string="Rental Line Start Date", tracking=True)
    rental_end_date = fields.Date(string="Rental Line End Date", tracking=True)
    next_bill_date = fields.Date(compute="_compute_next_bill_date", string="Next Bill Date", store=True, readonly=False)
    rental_status = fields.Selection(selection=[('draft', "Quotation"),
                                                ('sent', "Quotation Sent"),
                                                ('rent', "Rental Order"),
                                                ('sale', "Sale Order"),
                                                ('confirmed', "Confirmed"),
                                                ('finish', "Finished"),
                                                ('cancel', "Cancelled"),
                                                ], string="Rental Status", compute='_compute_rental_status',store=False)
    active = fields.Boolean(default=True)
    is_sale = fields.Boolean()
    parent_line = fields.Integer()
    rental_available_lot_ids = fields.Many2many('stock.lot', 'rental_available_lot_rel',
                                                compute="_compute_pickeable_lot_ids")
    rental_pickable_lot_ids = fields.Many2many('stock.lot',
                                               domain="[('id','in',rental_available_lot_ids),('reserved','!=',True)]")
    is_service_charge = fields.Boolean()
    importing_external_id = fields.Char(help="External Id Provided during importing")
    need_bill_importing = fields.Boolean()
    line_signature_status = fields.Selection(selection=[('initial', "Initial"),
                                                        ('delivery', "Delivery Sent"),
                                                        ('complete', "Completed"),
                                                        ],string="Signature Status",default="initial", store=True)
    daily_rate = fields.Float('Daily Rate')
    extended_amount  = fields.Float('Extended Amount',compute='_compute_rental_days_amount')
    rental_days = fields.Integer('Rental Days',store=True,readonly=False, compute='_compute_rental_days_amount')


    _sql_constraints = [
        ('rental_stock_coherence',
         "CHECK(NOT is_rental OR NOT is_service_charge OR qty_returned <= qty_delivered)",
         "You cannot return more than what has been picked up."),
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Supering Create function of sale order lines at the end"""
        if self._context.get('import_from_sheet'):
            return super().create(vals_list)
        for vals in vals_list:
            product_template_id = vals.get('product_template_id')
            product = self.env['product.template'].search([('id', '=', product_template_id)])
            is_sale = vals.get('is_sale')
            prod_price = 0

            # Check price list and distance range if mileage is enabled
            if product and not product.charges_ok and product.transportation_rate:
                order = self.env['sale.order'].browse(vals.get('order_id'))
                if order.mileage_enabled and order.pricelist_id and order.pricelist_id.distance_range_line_ids:
                    mileage = order.mileage
                    for distance_range in order.pricelist_id.distance_range_line_ids:
                        delivery_products = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                 ('service_category', '=',
                                                                                  'delivery')]).mapped('name')

                        pickup_products = self.env['product.template'].search([('charges_ok', '=', True),
                                                                               ('service_category', '=',
                                                                                'pickup')]).mapped('name')
                        if any(prod in distance_range.name.mapped('name') for prod in
                               delivery_products + pickup_products):
                            if distance_range.distance_end != 0:
                                if distance_range.distance_begin <= mileage <= distance_range.distance_end:
                                    prod_price = distance_range.transportation_rate
                            else:
                                if distance_range.pricelist_id.name == "WTR":
                                    prod_price = distance_range.transportation_rate
                                elif distance_range.distance_begin <= mileage:
                                    prod_price = mileage * distance_range.transportation_rate

            # Adding service charges while saving
            if product_template_id and not is_sale:
                product_charges = product.charges_ids
                products = self.env['product.product'].search([
                    ('charges_ok', '=', True),
                    ('service_category', 'in', ['delivery', 'pickup', ])
                ]).mapped('name')
                order = self.env['sale.order'].browse(vals.get('order_id'))
                if product_charges:
                    for prod in product_charges:
                        order.order_line.create({
                            'name': f"{prod.name} For {product.name}",
                            'sequence': vals.get('sequence') + 1,
                            'order_id': order.id,
                            'product_id': prod.id,
                            'product_uom_qty': vals.get('product_uom_qty'),
                            'price_unit': prod_price if prod.name in products else 0.00,
                            'display_type': False,
                            'parent_line': vals.get('sequence')
                        })
                # Fuel Surcharges
                if prod_price > 0:
                    products = self.env['product.product'].search([
                        ('charges_ok', '=', True), ('company_id', '=', self.env.company.id),
                        ('service_category', 'in', ['delivery-fuel', 'pickup-fuel'])])
                    # products = self.env['product.product'].search([
                    #     ('charges_ok', '=', True),('service_category', 'in', ['delivery-fuel', 'pickup-fuel'])])
                    for prod in products:
                        fuel_charge = order.fuel_surcharge_percentage
                        order.order_line.create({
                            'name': f"{prod.name} For {product.name}",
                            'sequence': vals.get('sequence') + 1,
                            'order_id': order.id,
                            'product_id': prod.id,
                            'product_uom_qty': vals.get('product_uom_qty'),
                            'price_unit': (prod_price * fuel_charge) / 100,
                            'display_type': False,
                            'parent_line': vals.get('sequence')
                        })

        # Call super at the end
        res = super().create(vals_list)
        # Update unit price based on price list
        for line in res:
            if line.display_type != 'line_section' and (not line.product_template_id.charges_ok):
                for vals in vals_list:
                    # for ensuring unique section name
                    if vals.get('display_type') == 'line_section' and vals.get('name'):
                        order_id = vals.get('order_id')
                        sequence = vals.get('sequence')
                        existing_sections = self.env['sale.order.line'].search([
                            ('order_id', '=', order_id),
                            ('display_type', '=', 'line_section'),
                            ('name', '=', vals.get('name')),
                            ('sequence', '!=', sequence),
                        ])
                        if existing_sections:
                            raise ValidationError(
                                f"The section name '{vals.get('name')}' must be unique within the sale order.")
                    # to calculate the main product's price according to the pricelist
                    if "display_type" in vals and vals['display_type'] != 'line_section':
                        product = self.env['product.template'].browse(vals.get('product_template_id'))
                        if product and not product.charges_ok and product.transportation_rate:
                            if product in line.order_id.pricelist_id.product_pricing_ids.product_template_id:
                                for product_pricing in line.order_id.pricelist_id.product_pricing_ids:
                                    if product_pricing.product_template_id == product and line.product_template_id == product:
                                        if (
                                                product_pricing.recurrence_id.duration == line.order_id.recurring_plan_id.billing_period_value and
                                                product_pricing.recurrence_id.unit == line.order_id.recurring_plan_id.billing_period_unit):
                                            line.price_unit = product_pricing.price
                                        elif (((product_pricing.recurrence_id.duration == 1) and (
                                                line.order_id.recurring_plan_id.billing_period_value == 28)) and
                                              ((product_pricing.recurrence_id.unit == 'month') and (
                                                      line.order_id.recurring_plan_id.billing_period_unit == 'day'))):
                                            line.price_unit = product_pricing.price
                                        elif (((product_pricing.recurrence_id.duration == 28) and (
                                                line.order_id.recurring_plan_id.billing_period_value == 1)) and
                                              ((product_pricing.recurrence_id.unit == 'day') and (
                                                      line.order_id.recurring_plan_id.billing_period_unit == 'month'))):
                                            line.price_unit = product_pricing.price
                                        elif product_pricing.recurrence_id.duration == 30 and product_pricing.recurrence_id.unit == 'day':
                                            line.price_unit = product_pricing.price
                                        elif product_pricing.recurrence_id.duration == 1 and product_pricing.recurrence_id.unit == 'day':
                                            line.price_unit = product_pricing.price
                            else:
                                if line.product_template_id == product:
                                    line.price_unit = product.list_price
                        else:
                            line.price_unit = product.list_price
        for line in res:
            if line.order_id.is_rental_order:
                line.is_service_charge = line.product_id.charges_ok
                # Apply header-level dates to the newly created lines
                # line.order_id.header_start_date = line.order_id.rental_start_date.astimezone(pytz.utc).replace(tzinfo=None)
                # line.order_id.header_return_date = line.order_id.rental_return_date.astimezone(pytz.utc).replace(tzinfo=None)
                # Extract header-level dates
                start_date = line.order_id.rental_start_date
                return_date = line.order_id.rental_return_date
                # Convert to UTC only if the datetime contains a time component
                if isinstance(start_date, datetime) and start_date.time() != datetime.min.time():
                    line.order_id.header_start_date = start_date.astimezone(pytz.utc).replace(tzinfo=None)
                else:
                    line.order_id.header_start_date = start_date  # Keep as is if only date

                if isinstance(return_date, datetime) and return_date.time() != datetime.min.time():
                    line.order_id.header_return_date = return_date.astimezone(pytz.utc).replace(tzinfo=None)
                else:
                    line.order_id.header_return_date = return_date  # Keep as is if only date
                if line.order_id.header_start_date and line.order_id.header_return_date and not (
                        line.rental_start_date or line.rental_end_date):
                    line.rental_start_date = line.order_id.header_start_date
                    line.rental_end_date = line.order_id.header_return_date
                if line.is_rental:
        # Calculate unit price based on daily price
                    if line.daily_rate>0 and line.order_id.recurring_plan_id:
                        billing_period_unit = line.order_id.recurring_plan_id.billing_period_unit
                        billing_period_value = line.order_id.recurring_plan_id.billing_period_value
                        if billing_period_unit == 'day':
                            line.price_unit = line.daily_rate * billing_period_value
                    qty = int(line.product_uom_qty)
                    for i in range(qty):
                        date_record_line = self.env['product.return.dates'].search([
                            ('order_id','=', line.order_id.id),
                            ('product_id','=', line.product_id.id),
                            ('serial_number','=', False),
                            ('quantity','=',1),
                            ('per_day_charges','=', line.price_unit),
                            ('order_line_id','=', line.id)
                        ])
                        if not date_record_line:
                            self.env['product.return.dates'].create([{
                                'order_id': line.order_id.id,
                                'product_id': line.product_id.id,
                                'serial_number': False,
                                'quantity': 1,
                                'per_day_charges': line.price_unit,
                                'order_line_id': line.id,
                            }])

        return res

    @api.depends('rental_start_date', 'rental_end_date', 'order_id.recurring_plan_id', 'order_id.bill_terms')
    def _compute_next_bill_date(self):
        """ To calculate next billing date based on recurring plan """
        for rec in self:
            if rec.order_id.bill_terms == "late":
                if rec.rental_start_date:
                    start_date = rec.rental_start_date

                    # by default, next_bill_date = today+28days
                    if not rec.order_id.recurring_plan_id:
                        rec.next_bill_date = date_utils.add(start_date, days=28)

                    if rec.order_id.recurring_plan_id.billing_period_unit == "day":
                        rec.next_bill_date = date_utils.add(start_date,
                                                            days=rec.order_id.recurring_plan_id.billing_period_value)

                    if rec.order_id.recurring_plan_id.billing_period_unit == "month":
                        rec.next_bill_date = date_utils.add(start_date,
                                                            months=rec.order_id.recurring_plan_id.billing_period_value)

                    if rec.order_id.recurring_plan_id.billing_period_unit == "year":
                        rec.next_bill_date = date_utils.add(start_date,
                                                            years=rec.order_id.recurring_plan_id.billing_period_value)
            else:
                if rec.rental_start_date:
                    if rec.qty_invoiced == 0:
                        start_date = rec.rental_start_date
                        rec.next_bill_date = start_date

    @api.depends('qty_delivered', 'qty_invoiced', 'qty_returned', 'state', 'is_sale')
    def _compute_rental_status(self):
        """To compute the Rental Status in the line level"""
        for line in self:
            if line.is_sale:
                line.rental_status = "sale"
            else:
                if not line.is_rental:
                    line.rental_status = False
                if line.state != 'sale':
                    line.rental_status = line.state
                elif line.state == 'sale' and line.qty_delivered == 0 and line.qty_invoiced == 0:
                    line.rental_status = 'confirmed'
                elif line.state == 'sale' and line.qty_delivered > 0:
                    line.rental_status = 'rent'
                if line.state == 'sale' and (
                        ( not line.need_bill_importing and line.qty_invoiced > 0) or
                        (line.qty_delivered > 0 and line.qty_delivered == line.qty_returned)):
                    line.rental_status = 'finish'
                if line.order_id.close_order:
                    line.rental_status = 'finish'
                # else:
                #     line.rental_status = 'cancel'
        section_prod = self.order_id.get_sections_with_products()
        for section, order_lines in section_prod.items():
            # Check if any line in the section is not charges_ok and has rental_status as 'finish'
            if any(
                    not line.product_template_id.charges_ok and line.rental_status == 'finish'
                    for line in order_lines
            ):
                for line in order_lines:
                    if line.qty_invoiced > 0:
                        line.write({'rental_status': 'finish'})

    @api.constrains('rental_start_date', 'rental_end_date')
    def check_rental_date(self):
        """ Validating Rental dates """
        for rec in self:
            if not rec.order_id.imported_order:
                if rec.rental_end_date and rec.rental_start_date and rec.rental_end_date < rec.rental_start_date:
                    raise ValidationError('The Return Date Must Be Greater Than Start Date.')

    @api.onchange('qty_delivered', 'qty_returned')
    def _onchange_quantities(self):
        """ Rental Start Date and Next Bill Date Validation """
        if self.order_id.is_rental_order and self.product_template_id and self.order_id.state != "draft":
            if not self.is_sale and not self.next_bill_date and not self.is_service_charge:
                raise ValidationError("Rental Start Date and Next Bill Date is mandatory before Delivery And Return")

    @api.constrains('qty_delivered', 'qty_returned')
    def check_service_products_qty(self):
        """ To update delivery charge's qty_delivered and dates"""
        # if self._context.get('import_from_sheet'):
        #     print("_context.get('import_from_sheet')")
        #     return
        # if not self.order_id.imported_order:
        section_prod = self.order_id.get_sections_with_products()
        for line in self:
            if line.order_id.is_rental_order and line.product_template_id and line.order_id.state != "draft" and not line.is_sale:
                # Find the section this product belongs to
                for section, order_line in section_prod.items():
                    if line in order_line and not line.product_template_id.charges_ok:
                        # Check if "rental delivery" product exists in the section
                        delivery_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                             ('service_category', '=',
                                                                              'delivery')]).mapped('name')
                        rental_delivery_lines = (line for line in order_line if
                                                 line.product_template_id.name in delivery_prod)
                        if rental_delivery_lines:
                            for rental_delivery_line in rental_delivery_lines:
                                # Update the qty_delivered for "rental delivery" product
                                sale_order_line = self.env['sale.order.line'].browse(rental_delivery_line._origin.id)
                                sale_order_line.write({
                                    # 'qty_delivered': line.qty_delivered -rental_delivery_line.qty_invoiced,
                                    'qty_delivered': line.qty_delivered - line.qty_returned,
                                    'next_bill_date': line.next_bill_date,
                                    'rental_start_date': line.rental_start_date,
                                    'rental_end_date': line.rental_end_date,
                                })
                        # Check if "delivery fuel surcharge" product exists in the section
                        delivery_fuel_surcharge_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                            ('service_category', '=',
                                                                                             'delivery-fuel')]).mapped('name')
                        delivery_fuel_surcharge_lines = (line for line in order_line if
                                                         line.product_template_id.name in delivery_fuel_surcharge_prod)
                        if delivery_fuel_surcharge_lines:
                            for delivery_fuel_surcharge_line in delivery_fuel_surcharge_lines:
                                # Update the qty_delivered for "delivery fuel surcharge" product
                                if rental_delivery_lines:
                                    for rental_delivery_line in rental_delivery_lines:
                                        sale_order_line.write({
                                            'qty_delivered': line.qty_delivered - rental_delivery_line.qty_invoiced,
                                            'next_bill_date': line.next_bill_date,
                                            'rental_start_date': line.rental_start_date,
                                            'rental_end_date': line.rental_end_date,
                                        })
                                else:
                                    sale_order_line = self.env['sale.order.line'].browse(
                                        delivery_fuel_surcharge_line._origin.id)
                                    sale_order_line.write({
                                        'qty_delivered': line.qty_delivered - delivery_fuel_surcharge_line.qty_invoiced,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                        # Check if "rental dwpp" product exists in the section
                        rental_dwpp_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                ('service_category', '=',
                                                                                 'dwpp')]).mapped('name')
                        rental_dwpp_lines = (line for line in order_line if
                                             line.product_template_id.name in rental_dwpp_prod)
                        if rental_dwpp_lines:
                            for rental_dwpp_line in rental_dwpp_lines:
                                # Update the qty_delivered for "rental dwpp" product
                                sale_order_line = self.env['sale.order.line'].browse(rental_dwpp_line._origin.id)
                                sale_order_line.write({
                                    'qty_delivered': line.qty_delivered - line.qty_returned,
                                    'next_bill_date': line.next_bill_date,
                                    'rental_start_date': line.rental_start_date,
                                    'rental_end_date': line.rental_end_date,

                                })
                        # Check if "rental pick-up" product exists in the section
                        rental_pickup_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                  ('service_category', '=',
                                                                                   'pickup')]).mapped('name')
                        rental_pickup_lines = (line for line in order_line if
                                               line.product_template_id.name in rental_pickup_prod)
                        if rental_pickup_lines:
                            for rental_pickup_line in rental_pickup_lines:
                                # Update the qty_delivered for "rental pickup" product
                                sale_order_line = self.env['sale.order.line'].browse(rental_pickup_line._origin.id)
                                if line.product_template_id.charges_in_first_invoice:
                                    sale_order_line.write({
                                        'qty_delivered': line.qty_delivered - rental_pickup_line.qty_invoiced,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                                else:
                                    sale_order_line.write({
                                        'qty_delivered': line.qty_returned - rental_pickup_line.qty_invoiced,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                        # Check if "pickup fuel surcharge" product exists in the section
                        pickup_fuel_surcharge_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                          ('service_category', '=',
                                                                                           'pickup-fuel')]).mapped(
                            'name')
                        pickup_fuel_surcharge_lines = (line for line in order_line if
                                                       line.product_template_id.name in pickup_fuel_surcharge_prod)
                        if pickup_fuel_surcharge_lines:
                            for pickup_fuel_surcharge_line in pickup_fuel_surcharge_lines:
                                # Update the qty_delivered for "pick up fuel surcharge" product
                                sale_order_line = self.env['sale.order.line'].browse(
                                    pickup_fuel_surcharge_line._origin.id)
                                if line.product_template_id.charges_in_first_invoice:
                                    sale_order_line.write({
                                        'qty_delivered': line.qty_delivered - pickup_fuel_surcharge_line.qty_invoiced,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,

                                    })
                                else:
                                    sale_order_line.write({
                                        'qty_delivered': line.qty_returned - pickup_fuel_surcharge_line.qty_invoiced,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                        # Check if 'no service category' product exists in the section
                        no_service_charge_prod = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                      ('service_category', '=',
                                                                                       None)]).mapped('name')
                        no_service_charge_prod_lines = (line for line in order_line if
                                                        line.product_template_id.name in no_service_charge_prod)
                        if no_service_charge_prod_lines:
                            for no_service_charge_prod_line in no_service_charge_prod_lines:
                                # Update the qty_delivered for "rental delivery" product
                                sale_order_line = self.env['sale.order.line'].browse(
                                    no_service_charge_prod_line._origin.id)
                                if sale_order_line and not sale_order_line.need_bill_importing:
                                    qty = line.qty_delivered - line.qty_invoiced
                                    sale_order_line.write({
                                        'qty_delivered': qty if qty > 0 else 0,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                                if sale_order_line and sale_order_line.need_bill_importing:
                                    qty = line.qty_delivered - line.qty_returned
                                    sale_order_line.write({
                                        'qty_delivered': qty if qty > 0 else 0,
                                        'next_bill_date': line.next_bill_date,
                                        'rental_start_date': line.rental_start_date,
                                        'rental_end_date': line.rental_end_date,
                                    })
                if line.qty_delivered >= line.qty_returned:
                    line.invoice_status = 'to invoice'

    @api.onchange('is_sale')
    def _onchange_is_sale(self):
        """ Change the product_uom_qty of service products while is_sale changes """
        service_charges = self.env['product.product'].search([('charges_ok', '=', True)])
        for charges in service_charges:
            if self.is_sale and self.product_template_id.name == charges.name:
                raise ValidationError("Can't sell Service charges")
        if self.is_sale:
            if self.order_id and self.sequence:
                # Search for lines with `parent_line` matching the current line's `sequence`
                lines_to_delete = self.env['sale.order.line'].search([
                    ('order_id', '=', self._origin.order_id.id),
                    ('parent_line', '=', self.sequence)
                ])
                lines_to_delete.write({
                    'active': False})
            self.price_unit = self.product_template_id.list_price
        else:
            lines_to_delete = self.env['sale.order.line'].search([
                ('order_id', '=', self._origin.order_id.id),
                ('parent_line', '=', self.sequence),
                ('active', '=', False)
            ])
            if lines_to_delete:
                lines_to_delete.write({
                    'active': True})
            # Setting the unit price for products
            for line in self:
                if line.display_type != 'line_section' and (not line.product_template_id.charges_ok):
                    product = self.product_template_id
                    # to check the price list and the pricing rule
                    if product and not product.charges_ok and product.transportation_rate and line.order_id.pricelist_id and line.order_id.pricelist_id.product_pricing_ids:
                        for range in line.order_id.pricelist_id.product_pricing_ids:
                            if range.product_template_id == product:
                                # Check the rental period in the pricelist and recurring plan in the order
                                pricelist_period_duration = range.recurrence_id.duration
                                pricelist_period_unit = range.recurrence_id.unit
                                order_recurring_duration = line.order_id.recurring_plan_id.billing_period_value
                                order_recurring_unit = line.order_id.recurring_plan_id.billing_period_unit
                                if (pricelist_period_duration == order_recurring_duration) and (
                                        pricelist_period_unit == order_recurring_unit):
                                    line.price_unit = range.price
                                if (pricelist_period_duration == 1) and (pricelist_period_unit == 'day'):
                                    line.price_unit = range.price
                    else:
                        line.price_unit = product.list_price
        if self.product_template_id and self.qty_delivered:
            raise ValidationError("Cannot change the order status after Delivery")

    def _fetch_order_lines(self, seq):
        return self._origin.order_id.order_line.filtered(lambda x: x.sequence == seq)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """ Change the product_uom_qty of service products while the main product's product_uom_qty changes """
        if self.product_template_id and self.product_template_id.charges_ok == False:
            section_prod = self.order_id.get_sections_with_products()
            for section, order_lines in section_prod.items():
                # Check if any line in the section matches the current product_template_id
                if any(line.product_template_id == self.product_template_id for line in order_lines):
                    for lines in order_lines:
                        order_line = self.env["sale.order.line"].browse(lines._origin.id)
                        price = lines.price_unit
                        if self.is_sale:
                            order_line.write({'product_uom_qty': 0})
                        else:
                            order_line.write({
                                'product_uom_qty': self.product_uom_qty,
                                'price_unit': price,
                            })
            if self.is_rental:
                if self.env['product.return.dates'].search(
                        [('order_line_id', '=', self._origin.id)]):
                    if len(self.env['product.return.dates'].search(
                            [('order_line_id', '=', self._origin.id)])) < int(self.product_uom_qty):
                        qty = int(self.product_uom_qty) - len(
                            self.env['product.return.dates'].search([('order_line_id', '=', self._origin.id)]))
                        for i in range(qty):
                            self.env['product.return.dates'].create([{
                                'order_id': self._origin.order_id.id,
                                'product_id': self._origin.product_id.id,
                                'serial_number': False,
                                'quantity': 1,
                                'per_day_charges': self._origin.price_unit,
                                'order_line_id': self._origin.id,
                            }])
                    elif len(self.env['product.return.dates'].search(
                            [('order_line_id', '=', self._origin.id)])) > int(self.product_uom_qty):
                        return_dates = self.env['product.return.dates'].search([
                            ('order_line_id', '=', self._origin.id),
                            ('serial_number', '=', False)
                        ], order='id desc')
                        excess = len(self.env['product.return.dates'].search([
                            ('order_line_id', '=', self._origin.id)
                        ])) - int(self.product_uom_qty)
                        c# Remove only the extra number of records without serial numbers
                        return_dates[:excess].unlink()

    @api.onchange('product_template_id', 'product_id')
    def _onchange_products(self):
        """ Setting the per day charge of the product as its unit price """
        if (self.product_template_id or self.product_id):
            if (not self.rental_start_date or self.rental_end_date):
                self.name = self.product_template_id.name
            else:
                self.name = self.product_template_id.name
            if self.product_template_id.description_sale:
                self.name += " [ " + self.product_template_id.description_sale + " ]"

    @api.depends('product_id', 'product_template_id','order_id.location_id')
    def _compute_pickeable_lot_ids(self):
        """ For computing the available lot numbers of the product """
        for line in self:
            if not line.product_id.charges_ok or line.display_type != 'line_section':
                location = line.order_id.location_id
                pickeable_lot_ids = self.env['stock.lot']._get_available_lots(line.product_id,
                                                                              line.order_id.warehouse_id.lot_stock_id)
                if location:
                    # Find lots in the selected location with positive quantity and not reserved
                    valid_quants = self.env['stock.quant'].search([
                        ('product_id', '=', line.product_id.id),
                        ('location_id', '=', location.id),
                        ('quantity', '>', 0),
                        ('reserved_quantity', '=', 0),
                        ('lot_id', 'in', pickeable_lot_ids.ids),
                    ])
                    valid_lot_ids = valid_quants.mapped('lot_id').ids
                    pickeable_lot_ids = pickeable_lot_ids.filtered(lambda lot: lot.id in valid_lot_ids)

                pickeable_lot_ids = pickeable_lot_ids.filtered(
                    lambda lot: (not lot.company_id or lot.company_id == line.order_id.company_id) and not lot.reserved
                )
                if pickeable_lot_ids:
                    line.rental_available_lot_ids = pickeable_lot_ids
                else:
                    line.rental_available_lot_ids = False
            else:
                line.rental_available_lot_ids = False

    def write(self, vals):
        """Supering Write function for reserving serial no. once it's added to the line
           and un-reserving once it is removed"""
        return_value = True
        if self._context.get('import_from_sheet'):
            return super().write(vals)
        for line in self:
            prev_lots = line.rental_pickable_lot_ids
            return_value = super().write(vals)
            current_lots = line.rental_pickable_lot_ids
            if current_lots:
                for lot in current_lots:
                    if lot not in line.pickedup_lot_ids:
                        lot.reserved = True
            if prev_lots:
                for lot in prev_lots:
                    if lot not in current_lots:
                        lot.reserved = False
            # to check the ordered qty and number of serial numbers selected
            if len(line.rental_pickable_lot_ids) > line.product_uom_qty:
                line.product_uom_qty = len(line.rental_pickable_lot_ids)
        return return_value

    def _move_serials(self, lot_ids, location_id, location_dest_id):
        """Move the given lots from location_id to location_dest_id.

        :param stock.lot lot_ids:
        :param stock.location location_id:
        :param stock.location location_dest_id:
        """
        if not lot_ids:
            return
        rental_stock_move = self.env['stock.move'].create([{
            'product_id': self.product_id.id,
            'product_uom_qty': len(lot_ids),
            'product_uom': self.product_id.uom_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': self.order_partner_id.id,
            'sale_line_id': self.id,
            'name': _("Rental move: %(order)s", order=self.order_id.name),
        }])

        for lot_id in lot_ids:
            lot_quant = self.env['stock.quant']._gather(self.product_id, location_id, lot_id)
            lot_quant = lot_quant.filtered(lambda quant: quant.quantity == 1.0)
            if not lot_quant:
                location_id = self.env['stock.location'].search(
                    [('company_id', '=', self.order_id.company_id.parent_id.id), ('name', '=', 'Stock')])
                # location_dest_id =self.order_id.company_id.parent_id.rental_loc_id
                rental_stock_move = self.env['stock.move'].create([{
                    'product_id': self.product_id.id,
                    'product_uom_qty': len(lot_ids),
                    'product_uom': self.product_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'partner_id': self.order_partner_id.id,
                    'sale_line_id': self.id,
                    'name': _("Rental move: %(order)s", order=self.order_id.name),
                }])
                lot_quant = self.env['stock.quant']._gather(self.product_id, location_id, lot_id)
                lot_quant = lot_quant.filtered(lambda quant: quant.quantity == 1.0)
                if not lot_quant:
                    raise ValidationError(
                        _("No valid quant has been found in location %(location)s for serial number %(serial_number)s!",
                          location=location_id.name, serial_number=lot_id.name))
                # Best fallback strategy??
                # Make a stock move without specifying quants and lots?
                # Let the move be created with the erroneous quant???
            # As we are using serial numbers, only one quant is expected
            ml = self.env['stock.move.line'].create(rental_stock_move._prepare_move_line_vals(reserved_quant=lot_quant))
            ml['quantity'] = 1

        rental_stock_move.picked = True
        rental_stock_move._action_done()

    def action_send_delivery_signature(self):
        """ Button action for sending Delivery signature request to the driver """
        for line in self:
            date_lines = self.env['product.return.dates'].search([
                ('order_line_id', '=', line.id),
                ('signature_status', '=', 'initial')])
            if date_lines:
                for date_line in date_lines:
                    if (date_line.signature_status == 'initial'):
                        if date_line.delivery_driver:
                            date_line.signature_status = 'delivery'
                            line.line_signature_status = 'delivery'
                        else:
                            raise ValidationError("Select a Delivery Driver")
                    # Taking the notes added inside the Internal Notes field and passing to the template
                    html_content = date_line.description
                    if html_content:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        plain_text = soup.get_text(separator=" ", strip=True)
                    else:
                        plain_text = ""
                    pdf_report = self.env.ref('rental_customization.action_delivery_pdf_slip')

                    data = {
                        'ticket_no': date_line.order_id.name,
                        'logo': date_line.order_id.company_id.logo,
                        'customer': date_line.order_id.partner_id.name,
                        'notes': plain_text,
                        'location': date_line.order_id.warehouse_id
                    }

                    content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
                        pdf_report.report_name,
                        res_ids=date_line.ids,
                        data=data,
                    )
                    attatchment = self.env['ir.attachment'].create([{
                        'name': 'delivery_slip',
                        'type': 'binary',
                        'datas': base64.b64encode(content).decode('utf-8'),
                        'store_fname': 'delivery_slip',
                        'res_model': date_line._name,
                        'res_id': date_line.id,
                        'mimetype': 'application/x-pdf'
                    }])

                    sign_template = self.env['sign.template'].create([{
                        'attachment_id': attatchment.id,
                        'sign_item_ids': [fields.Command.create({
                            'type_id': self.env.ref('sign.sign_item_type_signature').id,
                            'responsible_id': self.env.ref('sign.sign_item_role_customer').id,
                            'page': 1,
                            'posX': 0.288,
                            'posY': 0.715,
                            'width': 0.2,
                            'height': 0.05,
                        })],
                    }])

                    request = self.env['sign.request'].sudo().create([{
                        'template_id': sign_template.id,
                        'request_item_ids': [fields.Command.create({
                            'partner_id': date_line.delivery_driver.id,
                            'role_id': 1,
                            'mail_sent_order': 1})],
                        'reference': f"delivery_slip-{date_line.serial_number.name}",
                        'subject': f'Signature Request - delivery_slip-{date_line.serial_number.name}',
                        'message': False, 'message_cc': False,
                        'validity': fields.Datetime.today(),
                        'reminder': 7,
                        'reminder_enabled': False,
                        'reference_doc': f"sale.order,{date_line.order_id.id}"}])

                    if request.reference_doc:
                        model = request.reference_doc and self.env['ir.model']._get(request._name)
                    if model.is_mail_thread:
                        body = _("A signature request has been linked to this document: %s", request._get_html_link())
                        date_line.order_id.message_post(body=body)
                        body = _("%s has been linked to this sign request.", date_line.order_id._get_html_link())
                        request.message_post(body=body)
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': _("Nothing to send Delivery Signature requests"),
                        'sticky': True,
                        'params': {
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    },
                }
        # raise ValidationError('err')

    @api.constrains('next_bill_date', 'rental_start_date', 'rental_end_date')
    def check_service_products_next_bill_date(self):
        """ To update all section lines' next_bill_date when a service product is updated """
        for line in self:
            if (line.order_id.is_rental_order and line.product_template_id and line.order_id.state != "draft" and not
                 line.product_template_id.charges_ok ):
                section_prod = line.order_id.get_sections_with_products()
                # Find the section this service line belongs to
                for section, order_lines in section_prod.items():
                    if line in order_lines:
                        # Update all lines in the same section with the new next_bill_date
                        for sec_line in order_lines:
                            if sec_line != line and sec_line.next_bill_date != line.next_bill_date or sec_line.rental_end_date != line.rental_end_date:
                                sec_line.write({
                                    'next_bill_date': line.next_bill_date,
                                    'rental_start_date': line.rental_start_date,
                                    'rental_end_date': line.rental_end_date,
                                })
                        break

    @api.onchange('daily_rate')
    def _onchange_daily_rate(self):
        """ Calculate Price Unit based on daily_rate """
        self.price_unit = self.product_id.list_price
        if self.daily_rate > 0 and self.order_id.recurring_plan_id :
            billing_period_unit = self.order_id.recurring_plan_id.billing_period_unit
            billing_period_value = self.order_id.recurring_plan_id.billing_period_value
            if billing_period_unit== 'day':
                self.price_unit = self.daily_rate * billing_period_value
        else:
            self.price_unit = self.product_id.list_price
            self.daily_rate = 0

    @api.depends('rental_start_date', 'rental_end_date','rental_days', 'daily_rate')
    def _compute_rental_days_amount(self):
        """ To compute total days of rental and the Extended amount """
        for record in self:
            record.extended_amount = 0
            if record.rental_start_date and record.rental_end_date:
                start_date = fields.Date.from_string(record.rental_start_date)
                end_date = fields.Date.from_string(record.rental_end_date)
                record.rental_days = (end_date - start_date).days
            if record.daily_rate:
                record.extended_amount = record.rental_days * record.daily_rate

    @api.onchange('rental_start_date','rental_days')
    def _onchange_rental_days(self):
        """ Calculate Rental End date based on rental_start_date and total_days """
        for record in self:
            if record.rental_start_date and record.rental_days >= 0:
                record.rental_end_date = date_utils.add(record.rental_start_date, days=record.rental_days)