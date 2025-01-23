# -*- coding: utf-8 -*-

from itertools import product
from google.auth import default
from odoo import api, models, fields, Command
from odoo.tools.safe_eval import datetime


class RentalOrderWizardLine(models.TransientModel):
    """To add new fields in the rental order"""
    _inherit = 'rental.order.wizard.line'

    def _apply(self):
        """ Record the Delivery and Return dates in the Sale order Page;Date Details """
        for lines in self:
            sale_order = lines.order_line_id.order_id
            product = lines.order_line_id.product_template_id
            product_id = lines.order_line_id.product_id.id
            if lines.pickedup_lot_ids and lines['status'] == 'pickup':
                for lot in lines.pickedup_lot_ids:
                    for range in sale_order.pricelist_id.product_pricing_ids:
                        if range.product_template_id == product:
                            # Check the rental period in the pricelist and recurring plan in the order
                            pricelist_period_duration = range.recurrence_id.duration
                            pricelist_period_unit = range.recurrence_id.unit
                            if sale_order.bill_terms == 'late' and ((pricelist_period_duration == 1) and (pricelist_period_unit == 'day')):
                                date_lines = self.env['product.return.dates'].create([{
                                    'order_id': sale_order.id,
                                    'product_id': product_id,
                                    'serial_number': lot.id,
                                    'quantity': 1,
                                    'per_day_charges': lines.order_line_id.price_unit,
                                    'delivery_date': fields.Date.today(),
                                }])
                            if sale_order.bill_terms == 'late' and not((pricelist_period_duration == 1) and (pricelist_period_unit == 'day')):
                                date_lines = self.env['product.return.dates'].create([{
                                    'order_id': sale_order.id,
                                    'product_id': product.id,
                                    'serial_number': lot.id,
                                    'quantity': 1,
                                    'delivery_date': fields.Date.today(),
                                }])
                            elif  sale_order.bill_terms == 'advance':
                                date_lines = self.env['product.return.dates'].create([{
                                    'order_id': sale_order.id,
                                    'product_id': product.id,
                                    'serial_number': lot.id,
                                    'quantity': 1,
                                    'delivery_date': fields.Date.today(),
                                }])

                            stock_quant = self.env['stock.lot'].search(
                                [('name', '=', lot.name), ('product_id', '=', lines.product_id.id)])
                            if stock_quant and stock_quant.location_id.warehouse_id:
                                date_lines.update({
                                    'warehouse_id': stock_quant.location_id.warehouse_id
                                })
            if lines.returned_lot_ids and lines['status'] == 'return':
                                for lot in lines.returned_lot_ids:
                                    date_lines = self.env['product.return.dates'].search([
                                        ('order_id', '=', sale_order.id),
                                        ('serial_number', '=', lot.id),
                                    ])
                                    if date_lines:
                                        date_lines.update({
                                            'return_date': fields.Date.today()
                                        })
        return super()._apply()