# -*- coding: utf-8 -*-
from odoo import api, models, fields, Command


class StockLocation(models.Model):
    _inherit = 'stock.location'

    short_name = fields.Char()
    partner_id = fields.Many2one('res.partner',string="Address")