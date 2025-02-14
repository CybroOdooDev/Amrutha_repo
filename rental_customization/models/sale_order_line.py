# -*- coding: utf-8 -*-
from ast import literal_eval
from email.policy import default
from itertools import product
from venv import create
from datetime import datetime
from odoo import api, fields, models
import pytz
from odoo.tools import date_utils
from odoo.exceptions import ValidationError
from odoo.fields import Command


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    rental_start_date = fields.Date(string="Rental Start Date", tracking=True)
    rental_end_date = fields.Date(string="Rental End Date", tracking=True)
    next_bill_date = fields.Date(compute="_compute_next_bill_date", string="Next Bill Date", store=True,readonly=False)
    rental_status = fields.Selection(selection=[('draft', "Quotation"),
                                                ('sent', "Quotation Sent"),
                                                ('rent', "Rental Order"),
                                                ('sale', "Sale Order"),
                                                ('confirmed', "Confirmed"),
                                                ('finish', "Finished"),
                                                ('cancel', "Cancelled"),
                                                ],string="Rental Status",compute='_compute_rental_status',store=False)
    active = fields.Boolean(default=True)
    is_sale = fields.Boolean()
    parent_line = fields.Integer()
    rental_available_lot_ids = fields.Many2many('stock.lot','rental_available_lot_rel',compute="_compute_pickeable_lot_ids")
    rental_pickable_lot_ids = fields.Many2many(
        'stock.lot',domain="[('id','in',rental_available_lot_ids),('reserved','!=',True)]")
    is_service_charge = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        """Supering Create function of sale order lines at the end"""
        for vals in vals_list:
            product_template_id = vals.get('product_template_id')
            product = self.env['product.template'].search([('id', '=', product_template_id)])
            is_sale = vals.get('is_sale')
            prod_price = 0

            # Check price list and distance range if mileage is enabled
            if product and product.transportation_rate:
                order = self.env['sale.order'].browse(vals.get('order_id'))
                if order.mileage_enabled and order.pricelist_id and order.pricelist_id.distance_range_line_ids:
                    mileage = order.mileage
                    for range in order.pricelist_id.distance_range_line_ids:
                        delivery_product_name = self.env.ref('rental_customization.default_delivery_product').name
                        pickup_product_name = self.env.ref('rental_customization.default_pickup_product').name
                        if delivery_product_name in range.name.mapped(
                                'name') or pickup_product_name in range.name.mapped('name'):
                            if range.distance_end != 0:
                                if range.distance_begin <= mileage <= range.distance_end:
                                    prod_price = range.transportation_rate
                            else:
                                if range.distance_begin <= mileage:
                                    prod_price = mileage * range.transportation_rate

            # Adding service charges while saving
            if product_template_id and not is_sale:
                product_charges = product.charges_ids
                order = self.env['sale.order'].browse(vals.get('order_id'))
                if product_charges:
                    for prod in product_charges:
                        order.order_line.create({
                            'name': f"{prod.name} For {product.name}",
                            'sequence': vals.get('sequence') + 1,
                            'order_id': order.id,
                            'product_id': prod.id,
                            'product_uom_qty': vals.get('product_uom_qty'),
                            'price_unit': prod_price if prod.name in ('Rental Delivery', 'Rental Pick-Up') else 0.00,
                            'display_type': False,
                            'parent_line': vals.get('sequence')
                        })

                # Fuel Surcharges
                if prod_price > 0:
                    products = [
                        self.env.ref('rental_customization.delivery_fuel_surcharge_product'),
                        self.env.ref('rental_customization.pickup_fuel_surcharge_product')
                    ]
                    for prod in products:
                        fuel_charge = order.fuel_surcharge_percentage
                        order.order_line.create({
                            'name': f"{prod.name} For {product.name}",
                            'sequence': vals.get('sequence') + 1,
                            'order_id': order.id,
                            'product_id': prod.id,
                            'product_uom_qty': vals.get('product_uom_qty'),
                            # 'price_unit': (prod_price * 15) / 100,
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
                        if product and product.transportation_rate:
                            if product in line.order_id.pricelist_id.product_pricing_ids.product_template_id:
                                for range in line.order_id.pricelist_id.product_pricing_ids:
                                    if range.product_template_id == product and line.product_template_id == product:
                                        if (range.recurrence_id.duration == line.order_id.recurring_plan_id.billing_period_value and
                                                range.recurrence_id.unit == line.order_id.recurring_plan_id.billing_period_unit):
                                            line.price_unit = range.price
                                        elif (((range.recurrence_id.duration == 1) and (line.order_id.recurring_plan_id.billing_period_value == 28)) and
                                            ((range.recurrence_id.unit == 'month') and (line.order_id.recurring_plan_id.billing_period_unit == 'day'))):
                                            line.price_unit = range.price
                                        elif (((range.recurrence_id.duration == 28) and (line.order_id.recurring_plan_id.billing_period_value == 1 )) and
                                            ((range.recurrence_id.unit == 'day') and (line.order_id.recurring_plan_id.billing_period_unit == 'month'))):
                                            line.price_unit = range.price
                                        elif range.recurrence_id.duration == 1 and range.recurrence_id.unit == 'day':
                                            line.price_unit = range.price
                            else:
                                if line.product_template_id == product:
                                    line.price_unit = product.list_price
                        else:
                            line.price_unit = product.list_price

        for line in res:
            line.is_service_charge = line.product_id.charges_ok
            # Apply header-level dates to the newly created lines
            line.order_id.header_start_date = line.order_id.rental_start_date.astimezone(pytz.utc).replace(tzinfo=None)
            line.order_id.header_return_date = line.order_id.rental_return_date.astimezone(pytz.utc).replace(tzinfo=None)
            if line.order_id.header_start_date and line.order_id.header_return_date and not (
                    line.rental_start_date or line.rental_end_date):
                line.rental_start_date = line.order_id.header_start_date
                line.rental_end_date = line.order_id.header_return_date

        return res

    @api.depends('rental_start_date', 'rental_end_date', 'order_id.recurring_plan_id','order_id.bill_terms')
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

    @api.depends('qty_delivered', 'qty_invoiced', 'qty_returned', 'state','is_sale')
    def _compute_rental_status(self):
        """To compute the Rental Status in the line level"""
        for order in self:
            if order.is_sale:
                order.rental_status = "sale"
            else:
                if not order.is_rental:
                    order.rental_status = False
                if order.state != 'sale':
                    order.rental_status = order.state
                elif order.state == 'sale' and order.qty_delivered == 0 and order.qty_invoiced ==0:
                    order.rental_status = 'confirmed'
                elif order.state == 'sale' and order.qty_delivered > 0:
                    order.rental_status = 'rent'
                elif order.state == 'sale' and order.qty_delivered == 0 and order.qty_invoiced >0:
                    order.rental_status = 'finish'
                else:
                    order.rental_status = 'cancel'

    @api.constrains('rental_start_date', 'rental_end_date')
    def check_rental_date(self):
        """ Validating Rental dates """
        for rec in self:
            if rec.rental_end_date and rec.rental_start_date and rec.rental_end_date < rec.rental_start_date:
                raise ValidationError('The Return Date Must Be Greater Than Start Date.')

    @api.onchange('qty_delivered', 'qty_returned')
    def _onchange_quantities(self):
        """ Rental Start Date and Next Bill Date Validation """
        if self.order_id.is_rental_order and self.product_template_id and self.order_id.state != "draft":
            if not self.is_sale and  not self.next_bill_date:
                raise ValidationError("Rental Start Date and Next Bill Date is mandatory before Delivery And Return")

    @api.constrains('qty_delivered', 'qty_returned','next_bill_date','rental_start_date','rental_end_date' )
    def check_service_products_qty(self):
        """ To update delivery charge's qty_delivered and dates"""
        section_prod = self.order_id.get_sections_with_products()
        for line in self:
            if line.order_id.is_rental_order and line.product_template_id and line.order_id.state != "draft" and not line.is_sale:
                # Find the section this product belongs to
                for section, order_line in section_prod.items():
                    if line in order_line and not line.product_template_id.charges_ok:
                    # Check if "rental delivery" product exists in the section
                        rental_delivery_line = next(
                            (line for line in order_line if line.product_template_id.name == "Rental Delivery"), None
                        )
                        if rental_delivery_line:
                            # Update the qty_delivered for "rental delivery" product
                            sale_order_line = self.env['sale.order.line'].browse(rental_delivery_line._origin.id)
                            sale_order_line.write({
                                'qty_delivered': line.qty_delivered -rental_delivery_line.qty_invoiced,
                                'next_bill_date': line.next_bill_date,
                                'rental_start_date':line.rental_start_date,
                                'rental_end_date':line.rental_end_date,
                            })
                    # Check if "delivery fuel surcharge" product exists in the section
                        delivery_fuel_surcharge_line = next(
                            (line for line in order_line if line.product_template_id.name == "Delivery Fuel Surcharge"),
                            None
                        )
                        if delivery_fuel_surcharge_line:
                            # Update the qty_delivered for "delivery fuel surcharge" product
                            sale_order_line = self.env['sale.order.line'].browse(delivery_fuel_surcharge_line._origin.id)
                            sale_order_line.write({
                                'qty_delivered': line.qty_delivered - rental_delivery_line.qty_invoiced,
                                'next_bill_date': line.next_bill_date,
                                'rental_start_date': line.rental_start_date,
                                'rental_end_date': line.rental_end_date,
                            })

                    # Check if "rental dwpp" product exists in the section
                        rental_dwpp_line = next(
                            (line for line in order_line if line.product_template_id.name == "Rental DWPP"), None
                        )
                        if rental_dwpp_line:
                            # Update the qty_delivered for "rental dwpp" product
                            sale_order_line = self.env['sale.order.line'].browse(rental_dwpp_line._origin.id)
                            sale_order_line.write({
                                'qty_delivered': line.qty_delivered - line.qty_returned,
                                'next_bill_date': line.next_bill_date,
                                'rental_start_date': line.rental_start_date,
                                'rental_end_date': line.rental_end_date,

                            })

                    # Check if "rental pick-up" product exists in the section
                        rental_pickup_line = next(
                            (line for line in order_line if line.product_template_id.name == "Rental Pick-Up"), None
                        )
                        if rental_pickup_line:
                            # Update the qty_delivered for "rental dwpp" product
                            sale_order_line = self.env['sale.order.line'].browse(rental_pickup_line._origin.id)
                            if line.product_template_id.charges_in_first_invoice:
                                sale_order_line.write({
                                    'qty_delivered': line.qty_delivered - rental_pickup_line.qty_invoiced,
                                    'next_bill_date': line.next_bill_date,
                                    'rental_start_date':line.rental_start_date,
                                    'rental_end_date':line.rental_end_date,

                                })
                            else:
                                sale_order_line.write({
                                    'qty_delivered': line.qty_returned -rental_pickup_line.qty_invoiced,
                                    'next_bill_date': line.next_bill_date,
                                    'rental_start_date':line.rental_start_date,
                                    'rental_end_date':line.rental_end_date,
                                })

                    # Check if "pickup fuel surcharge" product exists in the section
                        pickup_fuel_surcharge_line = next(
                            (line for line in order_line if line.product_template_id.name == "Pick Up Fuel Surcharge"),
                            None
                        )
                        if pickup_fuel_surcharge_line:
                            # Update the qty_delivered for "pick up fuel surcharge" product
                            sale_order_line = self.env['sale.order.line'].browse(pickup_fuel_surcharge_line._origin.id)
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

    @api.onchange('is_sale')
    def _onchange_is_sale(self):
        """ Change the product_uom_qty of service products while is_sale changes """
        service_charges = self.env['product.product'].search([('charges_ok', '=',True)])
        for charges in service_charges:
            if  self.is_sale and self.product_template_id.name == charges.name:
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
                ('active','=', False)
            ])
            if lines_to_delete:
                lines_to_delete.write({
                    'active': True})
            # Setting theunit price for products
            for line in self:
                if line.display_type != 'line_section' and (not line.product_template_id.charges_ok):
                    product = self.product_template_id
                    # to check the price list and the pricing rule
                    if product and product.transportation_rate and line.order_id.pricelist_id and line.order_id.pricelist_id.product_pricing_ids:
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
        if self.product_template_id and  self.qty_delivered:
            raise ValidationError("Cannot change the order status after Delivery")

    def _fetch_order_lines(self, seq):
        return self._origin.order_id.order_line.filtered(lambda x: x.sequence == seq)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """ Change the product_uom_qty of service products while the main product's product_uom_qty changes """
        if self.product_template_id and self.product_template_id.charges_ok== False:
            product_template_id = self.product_template_id
            product_charges = self.env['product.template'].search([('id', '=', product_template_id.id)]).charges_ids
            if product_charges:
                # Search for existing lines with the name matching the pattern
                new_seq = self.sequence + 1
                matching_lines = self._fetch_order_lines(new_seq)
                for lines in matching_lines:
                    price = lines.price_unit
                    if self.is_sale:
                        lines.write({'product_uom_qty': 0})
                    else:
                        lines.write({'product_uom_qty': self.product_uom_qty})
                        lines.price_unit = price

    @api.onchange('product_template_id', 'product_id')
    def _onchange_products(self):
        """ Setting the per day charge of the product as its unit price """
        if (self.product_template_id or self.product_id):
            if (not self.rental_start_date or self.rental_end_date):
                self.name = self.product_template_id.name
            else:
                self.name = self.product_template_id.name

    @api.depends('product_id','product_template_id')  # Replace with a field that affects the domain
    def _compute_pickeable_lot_ids(self):
        """ For computing the available lot numbers of the product """
        for line in self:
            if not line.product_id.charges_ok or line.display_type != 'line_section':
                pickeable_lot_ids = self.env['stock.lot']._get_available_lots(line.product_id,
                                                                      line.order_id.warehouse_id.lot_stock_id)
                if pickeable_lot_ids:
                    line.rental_available_lot_ids = pickeable_lot_ids
                else:
                    line.rental_available_lot_ids = False
            else:
                line.rental_available_lot_ids = False

    def write(self, vals):
        """Supering Write function for reserving serial no. once it's added to the line
           and un-reserving once it is removed"""
        return_value = super().write(vals)
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