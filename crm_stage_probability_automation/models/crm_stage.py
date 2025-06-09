from odoo import models, fields, api

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    company_id = fields.Many2one(
        'res.company')
    check_company_boolean = fields.Char(compute='_compute_company_stages')
    is_lange_real_estate = fields.Boolean()

    @api.onchange('company_id')
    def _compute_company_stages(self):
        """conditionally visible the stages for
        Lange Real Estate and it's branches"""

        print("is there company", self.env.company.id)
        self.check_company_boolean = 0
        # self.is_lange_real_estate = False
        if self.env.company.id in [1,2,3,4,5]:
            self.is_lange_real_estate = True
            print("yesssss stage lange")
        else:
            self.is_lange_real_estate = False


