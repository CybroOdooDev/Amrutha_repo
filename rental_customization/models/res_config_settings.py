# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mileage_calculation = fields.Boolean("Mileage Calculation",config_parameter="rental_customization.mileage_calculation")
