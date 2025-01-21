# -*- coding: utf-8 -*-

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
    next_bill_date = fields.Date(compute="_compute_next_bill_date", string="Next Bill Date", store=True,
                                     readonly=False)
    rental_status = fields.Selection(selection=[('draft', "Quotation"),
                                                ('sent', "Quotation Sent"),
                                                ('rent', "Rental Order"),
                                                ('sale', "Sale Order"),
                                                ('confirmed', "Confirmed"),
                                                ('finish', "Finished"),
                                                ('cancel', "Cancelled"),
                                                ],
                                     string="Rental Status",
                                     compute='_compute_rental_status',
                                     store=False)
    active = fields.Boolean(default=True)
    is_sale = fields.Boolean()
    parent_line = fields.Integer()

    @api.model_create_multi
    def create(self, vals_list):
        """Supering Create function of sale order lines"""
        res = super().create(vals_list)
        # to calculate the main product's unit price based on PL
        for line in res:
            if line.display_type != 'line_section' and (not line.product_template_id.charges_ok):
                for vals in vals_list:
                    if vals['display_type'] != 'line_section':
                        product_template_id = vals.get('product_template_id')
                        product = self.env['product.template'].search([('id', '=', product_template_id)])
                    # to check the price list and the pricing rule
                        if product and product.transportation_rate and line.order_id.pricelist_id and line.order_id.pricelist_id.product_pricing_ids:
                            for range in line.order_id.pricelist_id.product_pricing_ids:
                                if range.product_template_id == product:
                                    #Check the rental period in the pricelist and recurring plan in the order
                                    pricelist_period_duration = range.recurrence_id.duration
                                    pricelist_period_unit = range.recurrence_id.unit
                                    order_recurring_duration = line.order_id.recurring_plan_id.billing_period_value
                                    order_recurring_unit = line.order_id.recurring_plan_id.billing_period_unit
                                    if (pricelist_period_duration==order_recurring_duration) and (pricelist_period_unit==order_recurring_unit):
                                        line.price_unit = range.price
                        else:
                            if product.is_per_day_charge:
                                line.price_unit = product.per_day_charge
                            else:
                                line.price_unit = product.list_price
        if res.order_id.is_rental_order:
            # Checking various validations and notifying errors
            line_section_count = sum(1 for vals in vals_list if vals.get('display_type') == 'line_section')
            if line_section_count > 1:
                raise ValidationError("Create one section with one Product,at a time")
            for vals in vals_list:
                # Ensuring section name is unique
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
                            f"The section name '{vals.get('name')}' must be unique within the sale order."
                        )

                product_template_id = vals.get('product_template_id')
                product = self.env['product.template'].search([('id', '=', product_template_id)])
                is_sale = vals.get('is_sale')
                prod_price = 0
                # to check the price list and the distance range
                if product and res.order_id.pricelist_id and res.order_id.pricelist_id.distance_range_line_ids:
                    mileage = res.order_id.mileage
                    for range in res.order_id.pricelist_id.distance_range_line_ids:
                        delivery_product_name = self.env.ref('rental_customization.default_delivery_product').name
                        pickup_product_name = self.env.ref('rental_customization.default_pickup_product').name
                        if delivery_product_name in range.name.mapped( 'name') or pickup_product_name in range.name.mapped('name'):
                            # if range.name.name == self.env.ref('rental_customization.default_delivery_product').name:
                            if range.distance_end != 0:
                                if range.distance_begin<= mileage <= range.distance_end :
                                    prod_price = range.transportation_rate
                            else:
                                if  range.distance_begin<= mileage:
                                    prod_price = mileage*range.transportation_rate

                # Adding service charges while saving
                if product_template_id and not is_sale:
                    product_charges = self.env['product.template'].search([('id', '=', product_template_id)]).charges_ids
                    # Delivery and Pick-Up charge
                    if product_charges:
                        sale_order = self.env['sale.order'].search([('id', '=', res.order_id.id)])
                        for prod in product_charges:
                            if prod.name in ('Rental Delivery','Rental Pick-Up'):
                                sale_order.order_line.create({
                                    'name': f"For {product.name}",
                                    'sequence': vals.get('sequence') + 1,
                                    'order_id': sale_order.id,
                                    'product_id': prod.id,
                                    'product_uom_qty': vals.get('product_uom_qty'),
                                    'price_unit': prod_price,
                                    'display_type': False,
                                    'parent_line': vals.get('sequence')
                                })
                            else:
                                sale_order.order_line.create({
                                'name': f"For {product.name}",
                                'sequence': vals.get('sequence')+1,
                                'order_id': sale_order.id,
                                'product_id': prod.id,
                                'product_uom_qty': vals.get('product_uom_qty'),
                                'price_unit': 0.00,
                                'display_type': False,
                                'parent_line' : vals.get('sequence')
                            })
                    # Fuel Surcharges
                    if prod_price>0:
                        products = [
                            self.env.ref('rental_customization.delivery_fuel_surcharge_product'),
                            self.env.ref('rental_customization.pickup_fuel_surcharge_product')
                        ]
                        for prod in products:
                            sale_order.order_line.create({
                                'name': f"For {product.name}",
                                'sequence': vals.get('sequence') + 1,
                                'order_id': sale_order.id,
                                'product_id': prod.id,
                                'product_uom_qty': vals.get('product_uom_qty'),
                                'price_unit': (prod_price*15)/100,
                                'display_type': False,
                                'parent_line': vals.get('sequence')
                            })

            # To apply the header level dates to the newly created line
            for line in res:
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
            lines_to_delete.write({
                'active': True})

            # Setting the per day charge for products
            if self.order_id.bill_terms == 'late' and self.product_template_id.is_per_day_charge:
                self.price_unit = self.product_template_id.per_day_charge

        if self.product_template_id and  self.qty_delivered:
            raise ValidationError("Cannot change the order status after Delivery")

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """ Change the product_uom_qty of service products while the main product's product_uom_qty changes """
        if self.product_template_id and self.product_template_id.charges_ok== False:
            product_template_id = self.product_template_id
            product = self.env['product.template'].search([('id', '=', product_template_id.id)]).name
            sale_order = self.env['sale.order'].search([('id', '=', self._origin.order_id.id)])
            product_charges = self.env['product.template'].search([('id', '=', product_template_id.id)]).charges_ids
            if product_charges:
                # Search for existing lines with the name matching the pattern
                matching_lines = self.env['sale.order.line'].search([
                    ('order_id', '=', sale_order.id),
                    ('name', '=', f"For {product}")
                ])
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
                self.name = " "
            else:
                self.name = " "

        if self.order_id.bill_terms == 'late' and self.product_template_id.is_per_day_charge and not self.is_sale:
            self.price_unit = self.product_template_id.per_day_charge

