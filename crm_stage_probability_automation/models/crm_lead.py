from odoo import models, api

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _update_lead_probabilities(self):
        leads = self.search([])

        main_company = self.env['res.company'].search([('name', '=', "Lange Real Estate")], limit=1)
        print("main company", main_company.id, "child companies", main_company.child_ids.ids)
        if not main_company:
            return

        valid_company_ids = [main_company.id] + main_company.child_ids.ids
        print("valid comapnies", valid_company_ids)

        for record in leads:
            if record.company_id.id in valid_company_ids:
                # continue
                prob = record.probability
                new_stage_name = False

                if 0 <= prob < 20:
                    print("lost yes")
                    new_stage_name = "Lost"
                elif 20 <= prob < 50:
                    print("cold yes")
                    new_stage_name = "Cold"
                elif 50 <= prob < 80:
                    print("warm yes")
                    new_stage_name = "Warm"
                elif 80 <= prob < 100:
                    print("Hot yes")
                    new_stage_name = "Hot"
                elif prob == 100:
                    print("Won yes")
                    new_stage_name = "Won"

                if new_stage_name:
                    stage = self.env['crm.stage'].search([('name', '=', new_stage_name)], limit=1)
                    if stage and record.stage_id != stage:
                        record.stage_id = stage.id  # Actually updates the stage
