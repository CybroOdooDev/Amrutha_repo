# -*- coding: utf-8 -*-
from odoo import api,models, fields, Command


class SaleOrder(models.Model):
    """To add new fields in the rental order"""
    _name = "distance.range.line"

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Price List Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Many2many('product.template', string="Products")
    distance_begin = fields.Integer(string="Distance Begin")
    distance_end = fields.Integer(string="Distance End")
    transportation_rate = fields.Float(string="Transportation Rate")