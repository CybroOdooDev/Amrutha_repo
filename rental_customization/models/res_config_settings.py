# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mileage_calculation = fields.Boolean("Mileage Calculation",config_parameter="rental_customization.mileage_calculation")
    fuel_surcharge_percentage = fields.Integer(default="15",config_parameter="rental_customization.fuel_surcharge_percentage")
    fuel_surcharge_unit = fields.Char(default='%', readonly=True)
