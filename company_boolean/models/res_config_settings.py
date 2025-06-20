 # -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one(
        comodel_name='res.company')

    is_shelter = fields.Boolean(
        string="Shelter Tab",
        related='company_id.is_shelter_company',
        readonly=False,
    )
