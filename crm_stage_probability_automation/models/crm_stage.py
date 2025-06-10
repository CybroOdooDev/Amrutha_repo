# from odoo import models, fields, api
#
# class CrmStage(models.Model):
#     _inherit = 'crm.stage'
#
#     company_ids = fields.Many2many('res.company', string="Allowed Companies")
#     check_company_boolean = fields.Char(compute='_compute_company_stages')
#     is_lange_real_estate = fields.Boolean()
#
#     @api.onchange('company_ids')
#     def _compute_company_stages(self):
#         """conditionally visible the stages for
#         Lange Real Estate and it's branches"""
#
#         print("is there company", self.env.company.id)
#         self.check_company_boolean = 0
#         # self.is_lange_real_estate = False
#         if self.env.company.id in [1,2,3,4,5]:
#             self.is_lange_real_estate = True
#             print("yesssss stage lange")
#         else:
#             self.is_lange_real_estate = False
#
#

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
