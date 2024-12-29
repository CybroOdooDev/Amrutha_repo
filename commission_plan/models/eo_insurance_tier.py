# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EOInsurance(models.Model):
    _name = "eo.insurance"
    _description = "Errors and Omissions Insurance"
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )
    from_amount = fields.Float(
        required=True, string="From Amount",
        help="From amount commission limit"
    )
    to_amount = fields.Float(
        required=True, string="To Amount", help="To amount commission limit"
    )
    eo_to_charge = fields.Float(required=True,string="E&O to Charge",
                                help="Errors and Omissions to charge")