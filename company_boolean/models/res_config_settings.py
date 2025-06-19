# # -*- coding: utf-8 -*-
#
# from odoo import api, fields, models
# class ResConfigSettings(models.TransientModel):
#     """Extension of 'res.config.settings' for configuring delivery settings."""
#     _inherit = 'res.config.settings'
#
#     is_shelter = fields.Boolean(
#         string='Shelter Tab',
#         related='company_id.is_shelter_company',
#         readonly=False  # Make it editable in the UI if needed
#     )
# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_shelter = fields.Boolean(
        string='Shelter Tab'
    )
