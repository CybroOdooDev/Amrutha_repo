# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from email.policy import default

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mileage_calculation = fields.Boolean("Mileage Calculation",config_parameter="rental_customization.mileage_calculation")
    fuel_surcharge_percentage = fields.Integer(default="15",config_parameter="rental_customization.fuel_surcharge_percentage")
    fuel_surcharge_unit = fields.Char(default='%', readonly=True)
    invoice_queue_follower_ids = fields.Many2many('res.users',string="Invoice Queue Followers")

    # , default = lambda self: self.env.ref('base.user_admin')
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'rental_customization.invoice_queue_follower', self.invoice_queue_follower_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        invoice_queue_follower_ids = params.get_param('rental_customization.invoice_queue_follower')
        res.update(
            invoice_queue_follower_ids=[(6, 0, eval(invoice_queue_follower_ids))
                          ] if invoice_queue_follower_ids else False,
        )
        return res