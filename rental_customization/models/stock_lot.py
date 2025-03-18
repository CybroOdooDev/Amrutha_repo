# -*- coding: utf-8 -*-
from odoo import api, models, fields, Command


class StockLot(models.Model):
    _inherit = 'stock.lot'

    reserved = fields.Boolean(store=True)