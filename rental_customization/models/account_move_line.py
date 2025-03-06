# -*- coding: utf-8 -*-
from odoo import models, fields,api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    rental_line_external_id = fields.Char(help="External Id of Rental Order Provided during importing")

    @api.onchange('quantity')
    def _onchange_product_qty(self):
        """ Change the product_uom_qty of service products while the main product's product_uom_qty changes """
        print(self.search_read([]))