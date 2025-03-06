# -*- coding: utf-8 -*-
from odoo import api,models, fields, Command


class PriceList(models.Model):
    """To add new fields in the rental order"""
    _inherit = "product.pricelist"

    distance_range_line_ids =  fields.One2many(
        comodel_name='distance.range.line',
        inverse_name='pricelist_id',
        string="Distance Range Lines",
        copy=True, auto_join=True)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        print(self.display_name)