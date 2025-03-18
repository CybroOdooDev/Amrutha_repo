# -*- coding: utf-8 -*-
from odoo import models, fields,api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    rental_line_external_id = fields.Char(help="External Id of Rental Order Provided during importing")