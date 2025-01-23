# -*- coding: utf-8 -*-
from google.auth import default
from odoo import api,models, fields, Command


class ProductTemplate(models.Model):
    """To add new fields in the rental order"""
    _inherit = "product.template"

    charges_in_first_invoice = fields.Boolean(string='Pick-Up Charge in First Invoice',
                                              help="Delivery & Pick-Up charges in the First invoice")
    charges_ids = fields.Many2many('product.product', string="Service Charges")
    charges_ok = fields.Boolean('Service Charge')
    transportation_rate = fields.Boolean(default=False,help="If selected,the unit price in the orders will be based"
                                                    " on the transportation rate specified in the selected price list.")

