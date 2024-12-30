# -*- coding: utf-8 -*-
from google.auth import default
from odoo import api,models, fields, Command


class ProductTemplate(models.Model):
    """To add new fields in the rental order"""
    _inherit = "product.template"

    charges_in_first_invoice = fields.Boolean(string='Pick-Up Charge in First Invoice',
                                              help="Delivery & Pick-Up charges in the First invoice", )
    charges_ids = fields.Many2many('product.product', string="Service Charges")
    charges_ok = fields.Boolean('Service Charge')
    is_per_day_charge = fields.Boolean(default=False)
    per_day_charge = fields.Float('Per day Charge', default=0.0,
        digits='Per day Charge',
        tracking=True,
        help="The per-day charge at which the product is rented to customers.",
    )

    @api.onchange('is_per_day_charge')
    def _onchange_is_per_day_charge(self):
        """ To add per day charge for product """
        if not self.is_per_day_charge:
            self.per_day_charge = 0