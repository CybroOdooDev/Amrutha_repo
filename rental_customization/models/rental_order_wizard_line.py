# -*- coding: utf-8 -*-

from itertools import product
from google.auth import default
from odoo import api, models, fields, Command
from odoo.tools.safe_eval import datetime
from odoo.exceptions import ValidationError



class RentalOrderWizardLine(models.TransientModel):
    """To add new fields in the rental order"""
    _inherit = 'rental.order.wizard.line'

    def _apply(self):
        """ Record the Delivery and Return dates in the Sale order Page; Date Details """
        for lines in self:
            sale_order = lines.order_line_id.order_id
            product = lines.order_line_id.product_template_id
            product_id = lines.order_line_id.product_id.id
            date_lines = False  # Initialize the variable
            if not product.charges_ok:
                if lines.pickedup_lot_ids and lines['status'] == 'pickup' and (
                        product.is_storable and product.tracking == 'serial'):
                    lines.order_line_id.rental_pickable_lot_ids.write({'reserved':False})
                    lines.order_line_id.update({
                        'rental_pickable_lot_ids': lines.pickedup_lot_ids | lines.order_line_id.pickedup_lot_ids
                    })
                    for lot in lines.pickedup_lot_ids:
                        lot.reserved = True
                        warehouse = lot.location_id.warehouse_id
                        if sale_order.pricelist_id.product_pricing_ids:
                            for range in sale_order.pricelist_id.product_pricing_ids:
                                if range.product_template_id == product:
                                    # Check rental period and recurring plan in order
                                    pricelist_period_duration = range.recurrence_id.duration
                                    pricelist_period_unit = range.recurrence_id.unit

                                    if sale_order.bill_terms == 'late' and (
                                            (pricelist_period_duration == 1) and (pricelist_period_unit == 'day')):
                                        if not self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                           ('order_id', '=', sale_order.id),('order_line_id', '=',
                                            lines.order_line_id.id)], limit=1):
                                            date_lines = self.env['product.return.dates'].create([{
                                                'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'per_day_charges': lines.order_line_id.price_unit,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id':lines.order_line_id.id,
                                            }])
                                        else:
                                            date_lines = self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                                       ('order_id', '=', sale_order.id),('order_line_id', '=',
                                                        lines.order_line_id.id)], limit=1)
                                            date_lines.update({'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'per_day_charges': lines.order_line_id.price_unit,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id':lines.order_line_id.id,})
                                    elif sale_order.bill_terms == 'late':
                                        if not self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                           ('order_id', '=', sale_order.id),('order_line_id', '=',
                                            lines.order_line_id.id)],limit=1):
                                            date_lines = self.env['product.return.dates'].create([{
                                                'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id': lines.order_line_id.id,
                                            }])
                                        else:
                                            date_lines = self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                                       ('order_id', '=', sale_order.id),('order_line_id', '=',
                                                        lines.order_line_id.id)], limit=1)
                                            date_lines.update({
                                                'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id': lines.order_line_id.id,
                                            })
                                    elif sale_order.bill_terms == 'advance':
                                        if not self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                           ('order_id', '=', sale_order.id),('order_line_id', '=',
                                             lines.order_line_id.id)],limit=1):
                                            date_lines = self.env['product.return.dates'].create([{
                                                'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id': lines.order_line_id.id,
                                            }])
                                        else:
                                            date_lines = self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                                       ('order_id', '=', sale_order.id),('order_line_id', '=',
                                                        lines.order_line_id.id)], limit=1)
                                            date_lines.update({'order_id': sale_order.id,
                                                'product_id': product_id,
                                                'serial_number': lot.id,
                                                'quantity': 1,
                                                'delivery_date': fields.Date.today(),
                                                'order_line_id': lines.order_line_id.id,})

                                # Handle case where no pricing record is found
                                else:
                                    if not self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                                                                ('order_id', '=', sale_order.id),
                                                                                ('order_line_id', '=',lines.order_line_id.id)
                                                                                ], limit=1):
                                        date_lines = self.env['product.return.dates'].create([{
                                            'order_id': sale_order.id,
                                            'product_id': product_id,
                                            'serial_number': lot.id,
                                            'quantity': 1,
                                            'delivery_date': fields.Date.today(),
                                            'order_line_id': lines.order_line_id.id,
                                        }])
                        else:
                            if not self.env['product.return.dates'].search([('serial_number', '=', lot.id),
                                                                            ('order_id', '=', sale_order.id),
                                                                            ('order_line_id', '=', lines.order_line_id.id)
                                                                            ], limit=1):
                                date_lines = self.env['product.return.dates'].create([{
                                    'order_id': sale_order.id,
                                    'product_id': product_id,
                                    'serial_number': lot.id,
                                    'quantity': 1,
                                    'delivery_date': fields.Date.today(),
                                    'order_line_id': lines.order_line_id.id,
                                }])
                        # Update warehouse_id if available
                        stock_quant = self.env['stock.lot'].search(
                            [('name', '=', lot.name), ('product_id', '=', lines.product_id.id)]
                        )
                        if stock_quant and warehouse and date_lines:
                            date_lines.update({
                                'warehouse_id': warehouse
                            })

                if lines.returned_lot_ids and lines['status'] == 'return' and product.is_storable:
                    for lot in lines.returned_lot_ids:
                        lot.reserved = False
                        date_lines = self.env['product.return.dates'].search([
                            ('order_id', '=', sale_order.id),
                            ('serial_number', '=', lot.id),
                        ])
                        if date_lines:
                            date_lines.update({'return_date': fields.Date.today()})
        return super()._apply()

    @api.model
    def _default_wizard_line_vals(self, line,status):
        """ To pass 'pickedup_lot_ids' to the wizard line """
        default_line_vals = super()._default_wizard_line_vals(line, status)
        remaining_lot_ids = list(set(line.rental_pickable_lot_ids.ids) - set(line.pickedup_lot_ids.ids))
        # Update default_line_vals with the filtered pickedup_lot_ids
        if status == 'pickup' and line.product_id.is_storable and line.product_id.tracking == 'serial':
            default_line_vals.update({
                'pickedup_lot_ids': remaining_lot_ids,
                'qty_delivered': len(remaining_lot_ids),
            })
        return default_line_vals