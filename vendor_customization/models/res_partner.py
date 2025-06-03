# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l099_not_available = fields.Boolean(string="1099 Not Available")

    @api.onchange('l099_not_available', 'box_1099_id')
    def _onchange_l099_not_available(self):
        for record in self:
            if record.l099_not_available:
                record.box_1099_id = False
