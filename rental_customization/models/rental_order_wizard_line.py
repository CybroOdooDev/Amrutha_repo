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
        res = super()._apply()
        for lines in self:
            sale_order = lines.order_line_id.order_id
            product = lines.order_line_id.product_id
            if sale_order.bill_terms == 'late' and product.is_per_day_charge:
                if lines.pickedup_lot_ids and lines['status'] == 'pickup':
                    for lot in lines.pickedup_lot_ids:
                        self.env['product.return.dates'].create([{
                            'order_id': sale_order.id,
                            'product_id': product.id,
                            'serial_number': lot.id,
                            'quantity': 1,
                            'per_day_charge': product.per_day_charge,
                            'delivery_date': fields.Date.today(),
                        }])
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

        return res

