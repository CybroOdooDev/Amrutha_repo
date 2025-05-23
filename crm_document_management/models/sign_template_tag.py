# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SignTemplateTAg(models.Model):
    _inherit = 'sign.template.tag'

    is_residential_sale = fields.Boolean(string="Residential sale")
    is_residential_purchase = fields.Boolean(string="Residential Purchase")
    is_commercial_sale = fields.Boolean(string="Commercial sale")
    is_commercial_purchase = fields.Boolean(string="Commercial Purchase")
    is_auction_sale = fields.Boolean(string="Auction sale")
    is_auction_purchase = fields.Boolean(string="Auction Purchase")