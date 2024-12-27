# -*- coding: utf-8 -*-
from importlib.metadata import requires

from google.auth import default
from odoo import api,models, fields, Command
from datetime import datetime



from odoo import models, fields

class ProductReturnDates(models.Model):
    _name = 'product.return.dates'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product',required=True)
    serial_number = fields.Many2one('stock.lot')
    quantity = fields.Integer()
    per_day_charge = fields.Float('Per Day Charge')
    total_days = fields.Integer('Total Days',compute='_compute_total_days_price',)
    total_price = fields.Float('Total Price',compute='_compute_total_days_price',)
    delivery_date = fields.Date('Delivery Date')
    return_date = fields.Date('Return Date')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Fetch the per_day_charge from the selected product"""
        if self.product_id and self.product_id.per_day_charge:
            self.per_day_charge = self.product_id.per_day_charge
        else:
            self.per_day_charge = 0.0

    @api.depends('delivery_date', 'return_date')
    def _compute_total_days_price(self):
        """ To compute total days of rental """
        for record in self:
            today = fields.Date.from_string(fields.date.today())
            delivery = fields.Date.from_string(record.delivery_date)
            if record.delivery_date and record.return_date:
                end = fields.Date.from_string(record.return_date)
                record.total_days = (end - delivery).days
            if record.delivery_date and not record.return_date:
                record.total_days = (today - delivery).days

            record.total_price = record.quantity * record.total_days * record.per_day_charge

