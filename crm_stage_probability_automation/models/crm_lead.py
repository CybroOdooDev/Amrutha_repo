from odoo import models, api, fields

class CRMLead(models.Model):
    _inherit = 'crm.lead'


    # stage_id = fields.Many2one(
    #     'crm.stage', string='Stage', index=True, tracking=True,
    #     compute='_compute_stage_id', readonly=False,
    #     copy=False, group_expand='_read_group_stage_ids', ondelete='restrict', domain="[('company_id','=', False)]")
    #
    # @api.depends('team_id', 'type')
    # def _compute_stage_id(self):
    #     for lead in self:
    #         if not lead.stage_id:
    #             lead.stage_id = lead._stage_find(domain=[('fold', '=', False)]).id

    def change_stages_for_lange(self):

        target_stage = self.env['crm.lead'].search([('company_id', 'in', [1,2,3,4,5])])
        print('target_stage', len(target_stage))
        for lead_stage in target_stage:
            if lead_stage.stage_id.name == "New":
                lead_stage.write({'stage_id': 19})
            if lead_stage.stage_id.name == "Qualified":
                lead_stage.write({'stage_id': 16})
                # lead_stage.stage_id.id = 16
            if lead_stage.stage_id.name == "Proposition":
                lead_stage.write({'stage_id': 20})
                # lead_stage.stage_id = 20
            print("lead_stage", lead_stage.stage_id)



    @api.model
    def _update_lead_probabilities(self):
        print("hyy")

    # target_stage = self.env['crm.lead'].search([('company_id', 'in', [1,2,3,4,5])])
        # print('target_stage', len(target_stage))
        # for lead_stage in target_stage:
        #     if lead_stage.stage_id.name == "New":
        #         lead_stage.write({'stage_id': 19})
        #     if lead_stage.stage_id.name == "Qualified":
        #         lead_stage.write({'stage_id': 16})
        #         # lead_stage.stage_id.id = 16
        #     if lead_stage.stage_id.name == "Proposition":
        #         lead_stage.write({'stage_id': 20})
        #         # lead_stage.stage_id = 20
        #     print("lead_stage", lead_stage.stage_id)
        #
        #
        #
        #     //////////
        # leads = self.search([])
        #
        # current_company = self.env.company
        # # if current_company.name == 'Residential':
        # #     for stage in self.env['crm.stage'].search([]):
        # #         if stage.name == 'New':
        # #             stage.name = 'Hot'
        # #         elif stage.name == 'Qualified':
        # #             stage.name = 'Cold'
        # # else:
        # #     for stage in self.env['crm.stage'].search([]):
        # #         if stage.name == 'Hot':
        # #             stage.name = 'New'
        # #         elif stage.name == 'Cold':
        # #             stage.name = 'Qualified'
        #
        # #
        # # main_company = self.env['res.company'].search([('name', '=', "Lange Real Estate")], limit=1)
        # # print("main company", main_company.id, "child companies", main_company.child_ids.ids)
        # # if not main_company:
        # #     return
        # #
        # # valid_company_ids = [main_company.id] + main_company.child_ids.ids
        # # print("valid comapnies", valid_company_ids)
        # #
        # # for record in leads:
        # #     if record.company_id.id in valid_company_ids:
        # #         # continue
        # #         prob = record.probability
        # #         new_stage_name = False
        # #
        # #         if 0 <= prob < 20:
        # #             print("lost yes")
        # #             new_stage_name = "Lost"
        # #         elif 20 <= prob < 50:
        # #             print("cold yes")
        # #             new_stage_name = "Cold"
        # #         elif 50 <= prob < 80:
        # #             print("warm yes")
        # #             new_stage_name = "Warm"
        # #         elif 80 <= prob < 100:
        # #             print("Hot yes")
        # #             new_stage_name = "Hot"
        # #         elif prob == 100:
        # #             print("Won yes")
        # #             new_stage_name = "Won"
        # #
        # #         if new_stage_name:
        # #             stage = self.env['crm.stage'].search([('name', '=', new_stage_name)], limit=1)
        # #             if stage and record.stage_id != stage:
        # #                 record.stage_id = stage.id  # Actually updates the stage
        #
        # print("hyy")
