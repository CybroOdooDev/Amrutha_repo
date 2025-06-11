# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    company_ids = fields.Many2many('res.company', string="Allowed Companies")
    is_lange_real_estate = fields.Boolean(compute='_compute_is_lange_real_estate', store=False)

    @api.depends_context('uid')  # triggers when user context changes
    def _compute_is_lange_real_estate(self):
        print('ff',self.env.context)
        """Mark stage as allowed for Lange Real Estate group companies."""
        for stage in self:
            stage.is_lange_real_estate = self.env.company.id in [1, 2, 3, 4, 5]
