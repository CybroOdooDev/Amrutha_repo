# -*- coding: utf-8 -*-

from importlib.metadata import requires
from itertools import product
from re import search
from google.auth import default
from odoo import api, models, fields, Command, _
import pytz
from odoo.tools import date_utils
from odoo.exceptions import ValidationError
import base64
import requests
import re
from odoo.tools import float_compare


RENTAL_STATUS = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('pickup', "Reserved"),
    ('return', "Delivered"),
    ('returned', "Returned"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    """To add new fields in the rental order"""
    _inherit = "sale.order"

    _sql_constraints = [(
        'rental_period_coherence',
        "CHECK(rental_start_date <= rental_return_date)",
        "The rental start date must be before the rental return date if any.",
    )]

    recurring_plan_id = fields.Many2one("rental.recurring.plan", string="Rental Recurring Plan",
                                        default=lambda self: self._get_default_recurring_plan())
    bill_terms = fields.Selection(selection=[('advance', "Advance Bill"), ('late', "Not Advance Bill")],
                                  string="Bill Terms", default='late')
    show_update_button = fields.Boolean(string="Show Update Button", default=False, store=True)
    header_start_date = fields.Date(help="Header level start date for lines")
    header_return_date = fields.Date(help="Header level end date for lines")
    date_records_line = fields.One2many(comodel_name='product.return.dates', inverse_name='order_id',
                                        string="Date Records Lines", copy=True, auto_join=True)
    mileage = fields.Float(help="Distance between Customer location and default warehouse", compute='_compute_mileage',
                           default=0)
    mileage_unit = fields.Selection(selection=[('ft', "ft"), ('m', "M"), ('km', "KM"), ('mi', "Miles")],
                                    compute='_compute_mileage', default='mi')
    mileage_enabled = fields.Boolean(string="Mileage Calculation Enabled", compute='_compute_mileage_enabled')
    fuel_surcharge_percentage = fields.Integer(compute='_compute_fuel_surcharge')
    fuel_surcharge_unit = fields.Char(default='%', readonly=True)
    rental_status = fields.Selection(
        selection=RENTAL_STATUS,
        string="Rental Status",
        compute='_compute_rental_status',
        store=True)
    imported_order = fields.Boolean(default=False)
    parent_company_id = fields.Many2one(
        'res.company',
        store=True,
        related = 'company_id.parent_id'
    )

    @api.depends('company_id')
    def _compute_mileage_enabled(self):
        """Check if the mileage calculation is enabled in setting"""
        Param = self.env['ir.config_parameter'].sudo()
        mileage_setting = Param.get_param('rental_customization.mileage_calculation', default=False)
        if mileage_setting:
            for record in self:
                record.mileage_enabled = True
        else:
            for record in self:
                record.mileage_enabled = False

    def _get_default_recurring_plan(self):
        """Get the default recurring plan (e.g., monthly)."""
        if not self.imported_order:
            default_plan = self.env['rental.recurring.plan'].search([('is_default', '=', 'True'),('company_id','=',[self.env.company.id])])
            return default_plan.id if default_plan else False
        else:
            return False

    @api.onchange('bill_terms')
    def _onchange_bill_terms(self):
        """Validation while changing Bill terms"""
        if self.state == 'sale':
            raise ValidationError("Can't change Bill Terms after Order Confirmation")

    @api.onchange('recurring_plan_id')
    def _onchange_recurring_plan_id(self):
        """Validation while changing Rental Recurring Plan"""
        if self.state == 'sale':
            raise ValidationError("Can't change Rental Recurring Plan after Order Confirmation")

    @api.onchange('rental_start_date', 'rental_return_date')
    def _onchange_rental_dates(self):
        """Show the button if rental dates change."""
        self.show_update_button = True

    def update_dates(self):
        """ 'Update Button' action - To apply changes in header level start date to the line level dates"""
        self.header_start_date = self.rental_start_date.astimezone(pytz.utc).replace(tzinfo=None)
        self.header_return_date = self.rental_return_date.astimezone(pytz.utc).replace(tzinfo=None)

        for order_line in self.order_line:
            if self.header_start_date and self.header_return_date:
                order_line.rental_start_date = self.header_start_date
                if not order_line.is_sale:
                    order_line.rental_end_date = self.header_return_date
                self.show_update_button = False
            if not self.header_start_date and self.header_return_date:
                raise ValueError("Start Date and End Date must be set on the order before updating lines.")

    @api.onchange('order_line')
    def _onchange_order_line(self):
        """ changing the invoice policy of a product as they are added to a Rental order """
        if self:
            if self.is_rental_order:
                for line in self.order_line:
                    if line.product_template_id:
                        line.product_template_id.invoice_policy = "delivery"

                # Ensuring one product within a section
                #     if not line.is_service_charge:
                #         current_sequence = line.sequence
                #         section_above = any(
                #             ol.sequence == current_sequence - 1 and ol.display_type == 'line_section'
                #             for ol in self.order_line
                #         )
                #
                #         if not section_above and not line.is_service_charge:
                #             raise ValidationError(
                #                 "Ensure each product is in a section and only one product per section.")

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
        if self._context.get('import_from_sheet'):
            return super(SaleOrder, self)._action_confirm()
        else:
            if not self.pricelist_id:
                raise ValidationError("Add a Price List")
            for line in self.order_line:
                if line.is_sale:
                    line.is_rental = False
                if line.product_template_id.charges_ok and not line.price_unit:
                    raise ValidationError("Add unit Price for Service Charges if applicable;otherwise remove the line.")
            self.order_line._action_launch_stock_rule()
            # validation for mileage calculation
            if self.mileage_enabled:
                delivery_address = 0
                if self.partner_id.child_ids:
                    for child in self.partner_id.child_ids:
                        if child.type == 'delivery':
                            delivery_address += 1
                    if delivery_address == 0:
                        raise ValidationError("Add a Delivery Address for the customer for Mileage calculation")
                else:
                    raise ValidationError("Add a Delivery Address for the customer for Mileage calculation")
            return super(SaleOrder, self)._action_confirm()

    def _prepare_confirmation_values(self):
        """ Over-writing the function - Prepare the sales order confirmation values."""
        if self._context.get('import_from_sheet'):
            return {
                'state': 'sale',
            }
        else:
            return {
                'state': 'sale',
                'date_order': fields.Datetime.now()
            }

    def action_add_sale_order(self):
        """ Adding sale order inside Rental order line """
        for line in self.order_line:
            if line.is_sale:
                line.is_rental = False
        self.order_line._action_launch_stock_rule()
        return super(SaleOrder, self)._action_confirm()

    def action_open_pickup(self):
        """ Pick-Up button validation """
        self.ensure_one()
        for line in self.order_line:
            if self._context.get('import_from_sheet'):
                continue
            if not line.is_sale and not line.next_bill_date and not line.display_type and not line.is_service_charge:
                raise ValidationError("Rental Start Date and Next Bill Date is mandatory before Delivery And Return")
            if line.product_template_id.charges_ok and not line.price_unit:
                raise ValidationError("Add unit Price for Service Charges if applicable;otherwise remove the line.")
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lines_to_pickup = self.order_line.filtered(
            lambda r:
            r.is_rental
            and not r.is_service_charge
            and r.product_type != 'combo'
            and float_compare(r.product_uom_qty, r.qty_delivered, precision_digits=precision) > 0)
        return self._open_rental_wizard('pickup', lines_to_pickup.ids)

    def action_open_return(self):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lines_to_return = self.order_line.filtered(
            lambda r:
            r.is_rental
            and not r.is_service_charge
            and r.product_type != 'combo'
            and float_compare(r.qty_delivered, r.qty_returned, precision_digits=precision) > 0)
        return self._open_rental_wizard('return', lines_to_return.ids)

    def _open_rental_wizard(self, status, order_line_ids):
        """over-writting the '_open_rental_wizard' function to change the pick-up wizard name"""
        context = {
            'order_line_ids': order_line_ids,
            'default_status': status,
            'default_order_id': self.id,
        }
        return {
            'name': _('Validate a delivery') if status == 'pickup' else _('Validate a return'),
            'view_mode': 'form',
            'res_model': 'rental.order.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    def generate_recurring_bills(self):
        """Continuous Bill creation based on the selected Rental recurring plan"""
        service_prod = self.env['product.product'].search([('charges_ok', '=', True),('service_category', 'in', ['delivery-fuel', 'pickup-fuel','delivery','pickup','dwpp'])]).mapped('name')
        today = fields.Date.today()
        main_prod = None
        lines_to_invoice = self.env['sale.order.line'].search([])

        if self._context.get('button_action'):
            filtered_order_lines = lines_to_invoice.filtered(
                lambda line: ((line.next_bill_date) or line.is_sale)
                             and line.order_id.state == "sale" and line.qty_delivered != 0
            )
        else:
            filtered_order_lines = lines_to_invoice.filtered(
                lambda line: ((line.next_bill_date and line.next_bill_date <= today) or line.is_sale) and line.order_id.state == "sale" and line.qty_delivered != 0
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
                for section, order_line in section_prod.items():
                    if line in order_line and line.qty_delivered:
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

                        if not line.is_sale and line.product_template_id.charges_ok == True:
                            invoice_vals['invoice_line_ids'].append(Command.create(
                                line._prepare_invoice_line(
                                    name=f"Rental Service Charges for {main_prod}",
                                    product_id=line.product_id.id,
                                    price_unit=line.price_unit,
                                    quantity=line.qty_delivered - line.qty_returned,
                                )
                            ))
                        # if (
                        #         line.product_template_id.name == "Rental Delivery" or line.product_template_id.name == "Rental Pick-Up"
                        #         or line.product_template_id.name == "Delivery Fuel Surcharge" or line.product_template_id.name == "Pick Up Fuel Surcharge"):
                        #     line.qty_delivered = 0
                        # if line.is_service_charge and line.product_template_id.name not in service_prod:
                        #     line.qty_delivered = 0

            # Removing lines with zero qty and zero price from the invoice
            invoice_vals['invoice_line_ids'] = [
                vals for vals in invoice_vals['invoice_line_ids']
                if vals[2].get('quantity', 0.0) != 0.0 and vals[2].get('price_unit', 0.0) != 0.0
            ]
            # Check if any product in invoice lines has charges_ok = False
            has_non_charge_product = any(
                self.env['product.product'].browse(vals[2].get('product_id')).charges_ok == False
                for vals in invoice_vals['invoice_line_ids']
            )

            # Create invoice only if there is at least one non-chargeable product
            if has_non_charge_product:
                invoice = self.env['account.move'].create(invoice_vals)
            # Updating the Next bill date
                if invoice:
                    if invoice.invoice_payment_term_id:
                        invoice._onchange_invoice_payment_term_id()

                    sale_order = invoice.line_ids.sale_line_ids.order_id
                    for lines in invoice.line_ids.sale_line_ids:
                        if not lines.product_template_id.charges_ok:
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

    @api.depends('partner_id', 'partner_id.city', 'warehouse_id', 'warehouse_id.partner_id.city', 'mileage_enabled')
    def _compute_mileage(self):
        """ To compute the Mileage if only the boolean field inside the setting is enabled """
        try:
            if self.mileage_enabled:
                api_key = "AIzaSyDOX3JC_DL4alKis0q-Xtb5qSeKiNZAEUI"
                if self:
                    for order in self:
                        origin = order.warehouse_id.partner_id.city
                        if order.partner_shipping_id and (order.partner_shipping_id != order.partner_id):
                            if order.partner_shipping_id.street:
                                destination = order.partner_shipping_id.street
                            elif order.partner_shipping_id.street2:
                                destination = order.partner_shipping_id.street2
                            elif order.partner_shipping_id.city:
                                destination = order.partner_shipping_id.city
                            elif order.partner_shipping_id.state_id:
                                destination = order.partner_shipping_id.name
                            elif order.partner_shipping_id.country_id:
                                destination = order.partner_shipping_id.name
                            if origin and destination:
                                url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                                params = {
                                    "origins": origin,
                                    "destinations": destination,
                                    "units": "imperial",
                                    "key": api_key,
                                }
                                response = requests.get(url, params=params)
                                if response.status_code == 200:
                                    data = response.json()
                                    if data["destination_addresses"] != data["origin_addresses"]:
                                        if data["rows"][0]["elements"][0]["status"] != 'ZERO_RESULTS' and \
                                                data["rows"][0]["elements"][0]["status"] != 'NOT_FOUND':
                                            # by road transportations only
                                            distance_text = data["rows"][0]["elements"][0]["distance"]["text"]
                                            distance_parts = distance_text.split()
                                            if distance_parts:
                                                order.mileage = float(distance_parts[0].replace(',', ''))
                                                order.mileage_unit = distance_parts[1]
                                                return data
                                            else:
                                                order.mileage = 0
                                                order.mileage_unit = 'mi'
                                                return {"error": f"HTTP {response.status_code}: {response.text}"}
                                        else:
                                            order.mileage = 0
                                            order.mileage_unit = 'ft'
                                    else:
                                        order.mileage = 0
                                        order.mileage_unit = 'ft'
                                else:
                                    order.mileage = 0
                                    order.mileage_unit = 'ft'
                            else:
                                order.mileage = 0
                                order.mileage_unit = 'ft'
                        else:
                            order.mileage = 0
                            order.mileage_unit = 'ft'
            else:
                self.mileage = None
                self.mileage_unit = None
        except:
            self.mileage = None
            self.mileage_unit = None
            pass

    def action_update_prices(self):
        """ Calculating unit price of Main product and service charges according to the Mileage and Price list """
        res = super(SaleOrder, self).action_update_prices()
        if self.pricelist_id:
            for line in self.order_line:
                if line.display_type != 'line_section' and (
                not line.product_template_id.charges_ok) and line.product_template_id.transportation_rate:
                    product = line.product_template_id
                    if product and not product.charges_ok and product.transportation_rate and self.pricelist_id and self.pricelist_id.product_pricing_ids:
                        for range in self.pricelist_id.product_pricing_ids:
                            if range.product_template_id == product:
                                # Check the rental period in the pricelist and recurring plan in the order
                                pricelist_period_duration = range.recurrence_id.duration
                                pricelist_period_unit = range.recurrence_id.unit
                                order_recurring_duration = line.order_id.recurring_plan_id.billing_period_value
                                order_recurring_unit = line.order_id.recurring_plan_id.billing_period_unit
                                if (pricelist_period_duration == order_recurring_duration) and (
                                        pricelist_period_unit == order_recurring_unit):
                                    line.price_unit = range.price
                elif line.display_type != 'line_section' and (line.product_template_id.charges_ok):
                    if self.mileage_enabled:
                        product = line.product_template_id
                        # to check the price list and the distance range
                        if product and self.pricelist_id and self.pricelist_id.distance_range_line_ids:
                            mileage = self.mileage
                            for range in self.pricelist_id.distance_range_line_ids:
                                # delivery_product_name = self.env.ref('rental_customization.default_delivery_product').name
                                delivery_product_name = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                             ('service_category', '=',
                                                                                              'delivery')]).mapped(
                                    'name')
                                # pickup_product_name = self.env.ref('rental_customization.default_pickup_product').name
                                pickup_product_name = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                           ('service_category', '=',
                                                                                            'pickup')]).mapped('name')
                                # delivery_fuel_surcharge = self.env.ref(
                                # 'rental_customization.delivery_fuel_surcharge_product').name
                                delivery_fuel_surcharge = self.env['product.template'].search(
                                    [('charges_ok', '=', True),
                                     ('service_category', '=', 'delivery-fuel')]).mapped('name')
                                # pickup_fuel_surcharge = self.env.ref(
                                #     'rental_customization.pickup_fuel_surcharge_product').name
                                pickup_fuel_surcharge = self.env['product.template'].search([('charges_ok', '=', True),
                                                                                             ('service_category', '=',
                                                                                              'pickup-fuel')]).mapped(
                                    'name')
                                fuel_charge = self.fuel_surcharge_percentage
                                if set(delivery_product_name) & set(range.name.mapped('name')) or set(
                                        pickup_product_name) & set(range.name.mapped('name')):
                                    if line.product_template_id.name in delivery_product_name or line.product_template_id.name in pickup_product_name:
                                        if range.distance_end != 0:
                                            if range.distance_begin <= mileage <= range.distance_end:
                                                line.price_unit = range.transportation_rate
                                        else:
                                            if range.distance_begin <= mileage:
                                                line.price_unit = mileage * range.transportation_rate
                                        price_unit = line.price_unit
                                    if line.product_template_id.name in delivery_fuel_surcharge or line.product_template_id.name in pickup_fuel_surcharge:
                                        line.price_unit = (price_unit * fuel_charge) / 100
                # res = super(SaleOrder, self).action_update_prices()
                elif line.display_type != 'line_section' and not line.product_template_id.transportation_rate and not line.product_template_id.charges_ok:
                    line.price_unit = line.product_template_id.list_price
        return res

    @api.depends('company_id')
    def _compute_fuel_surcharge(self):
        """To access the Fuel Surcharge Configured in the settings"""
        Params = self.env['ir.config_parameter'].sudo()
        fuel_surcharge_setting = Params.get_param('rental_customization.fuel_surcharge_percentage')
        self.fuel_surcharge_percentage = fuel_surcharge_setting if fuel_surcharge_setting else 15