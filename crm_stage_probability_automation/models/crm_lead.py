from odoo import models, api, fields

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    stage_company_ids = fields.Many2many('res.company', string= "Stage companies", compute="_compute_company_stages")

    @api.depends('tag_ids')
    def _compute_company_stages(self):
        """"""
        for record in self:
              record.stage_company_ids = [(6,0, [self.company_id.id])]

        # main_company = self.env['res.company'].search([('name', '=', "Lange Real Estate")], limit=1)
        # print("main company", main_company.id, "child companies", main_company.child_ids.ids)
        # if not main_company:
        #     return
        # valid_company_ids = [main_company.id] + main_company.child_ids.ids
        # print("valid comapnies", valid_company_ids)
        # print("valid comapnies", self)
        # for record in self:
        #     print('HAII')
        #     if record.company_id.id in valid_company_ids:
        #         prob = record.probability
        #         print('prob',prob)
        #         print('prob',prob)
        #         if 0 <= prob < 20:
        #             print("Lost - setting stage", record.name)
        #             print("Lost - setting stage", record.stage_id)
        #             # record.sudo().write({
        #             #     'stage_id':5,
        #             # })
        #             print('kkk')
        #             # record.stage_id.id = 5
        #         elif 20 <= prob < 50:
        #             print("ff")
        #             record.stage_id = self.env['crm.stage'].browse(19).id
        #
        #     #     elif 50 <= prob < 80:
        #     #         print("fffss")
        #     #         # record.stage_id = 16
        #     #     elif 80 <= prob < 100:
        #     #         print("pppp")
        #     #         # record.stage_id = 20
        #     #     elif prob == 100:
        #     #         print("yuyu")
        #     #     else:
        #     #         pass


    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        print("yaahhhh it's working")
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        # stage_ids = stages.sudo()._search(search_domain, order=stages._order)
        # if self.env.context.get('active_ids'):
        if self.env.company.id in [1, 2, 3, 4, 5]:
            # print("company rssss")
            return stages.browse([19, 16, 20, 4, 5])
        else:
            stage_ids = stages.sudo()._search(search_domain, order=stages._order)
            stage_ids = [stage_id for stage_id in stage_ids if stage_id not in [19, 16, 20]]
            # print("stage_idsss", stage_ids)
            return stages.browse(stage_ids)

    def change_stages_for_lange(self):
        """function for scheduled action to change the
        stage of all previous leads to new stages"""

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



    @api.depends('probability')
    def _update_lead_probabilities(self):
        print("hyy")

    # target_stage = self.env['crm.lead'].search([('company_id', 'in', [1,2,3,4,5])])
    #     print('target_stage', len(target_stage))
    #     for lead_stage in target_stage:
    #         if lead_stage.stage_id.name == "New":
    #             lead_stage.write({'stage_id': 19})
    #         if lead_stage.stage_id.name == "Qualified":
    #             lead_stage.write({'stage_id': 16})
    #             # lead_stage.stage_id.id = 16
    #         if lead_stage.stage_id.name == "Proposition":
    #             lead_stage.write({'stage_id': 20})
    #             # lead_stage.stage_id = 20
    #         print("lead_stage", lead_stage.stage_id)

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
        # leads = self.search([])
        # main_company = self.env['res.company'].search([('name', '=', "Lange Real Estate")], limit=1)
        # print("main company", main_company.id, "child companies", main_company.child_ids.ids)
        # if not main_company:
        #     return
        # #
        # valid_company_ids = [main_company.id] + main_company.child_ids.ids
        # print("valid comapnies", valid_company_ids)
        # print("valid comapnies", self)
        # #
        # for record in self:
        #     print('HAII')
        #     if record.company_id.id in valid_company_ids:
        #         prob = record.probability
        #         # print("probability", prob)
        #
        # #
        #         if 0 <= prob < 20:
        #             print("Lost - setting stage", record.name)
        #             record.stage_id = 5
        #         elif 20 <= prob < 50:
        #             print("ff")
        #             # record.stage_id = 19
        #         elif 50 <= prob < 80:
        #             print("fffss")
        #             # record.stage_id = 16
        #         elif 80 <= prob < 100:
        #             print("pppp")
        #             # record.stage_id = 20
        #         elif prob == 100:
        #             print("yuyu")
        #             # record.stage_id = 4
        #             # record.stage_id = 4
        #
        #
        # #         # if new_stage_name:
        #         #     stage = self.env['crm.stage'].search([('name', '=', new_stage_name)], limit=1)
        #         #     if stage and record.stage_id != stage:
        #         #         record.stage_id = stage.id  # Actually updates the stage
        #
        # # print("hyy")
