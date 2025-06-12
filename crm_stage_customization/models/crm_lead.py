# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo import Command


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    stage_company_ids = fields.Many2many('res.company', string= "Stage companies", compute="_compute_company_stages")

    @api.onchange('probability','expected_revenue')
    def _onchange_probability(self):
        """function to change the status bar based on probability"""
        for record in self:
            prob = record.probability
            if 0 <= prob < 20:
                record._origin.stage_id = (self.env.ref('crm_stage_customization.crm_stage_lang_5').id)

            elif 20 <= prob < 50:
                record._origin.stage_id = (self.env.ref('crm_stage_customization.crm_stage_lang_2').id)

            elif 50 <= prob < 80:
                record._origin.stage_id = (self.env.ref('crm_stage_customization.crm_stage_lang_3').id)

            elif 80 <= prob < 100:
                record._origin.stage_id = (self.env.ref('crm_stage_customization.crm_stage_lang_4').id)

            elif prob == 100:
                record._origin.stage_id = (self.env.ref('crm.stage_lead4').id)


    @api.depends('tag_ids','probability','expected_revenue')
    def _compute_company_stages(self):
        """compute to show the status bar stages based on selected company from staging"""
        for record in self:
              record.stage_company_ids = [(6,0, [self.company_id.id])]

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded

        #arrange the lange real estate and it's branches based on the probability
        leads = self.env['crm.lead'].search([('company_id', 'in', [1,2,3,4,5])])
        for record in leads:
            prob = record.probability
            if 0 <= prob < 20:
                self.env.cr.execute("""
                                UPDATE crm_lead
                                SET stage_id = %s
                                WHERE id = %s
                            """, ((self.env.ref('crm_stage_customization.crm_stage_lang_5').id), record.id))
            elif 20 <= prob < 50:
                print('kkkkaaa')
                self.env.cr.execute("""
                                UPDATE crm_lead
                                SET stage_id = %s
                                WHERE id = %s
                            """, ((self.env.ref('crm_stage_customization.crm_stage_lang_2').id), record.id))

            elif 50 <= prob < 80:
                print("16")
                self.env.cr.execute("""
                                UPDATE crm_lead
                                SET stage_id = %s
                                WHERE id = %s
                            """, ((self.env.ref('crm_stage_customization.crm_stage_lang_3').id), record.id))

            elif 80 <= prob < 100:
                print("20")
                self.env.cr.execute("""
                               UPDATE crm_lead
                               SET stage_id = %s
                               WHERE id = %s
                           """, ((self.env.ref('crm_stage_customization.crm_stage_lang_4').id), record.id))

            elif prob == 100:
                self.env.cr.execute("""
                               UPDATE crm_lead
                               SET stage_id = %s
                               WHERE id = %s
                           """, ((self.env.ref('crm.stage_lead4').id), record.id))

        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # switch kanban pipeline states for lang real estate and it's branches
        if self.env.company.id in [1, 2, 3, 4, 5]:
            # return stages.browse([19, 16, 20, 4, 5])
            return stages.browse([(self.env.ref('crm_stage_customization.crm_stage_lang_5').id), (self.env.ref('crm_stage_customization.crm_stage_lang_2').id), (self.env.ref('crm_stage_customization.crm_stage_lang_3').id),
                                  (self.env.ref('crm_stage_customization.crm_stage_lang_4').id), (self.env.ref('crm.stage_lead4').id)])
        else:
            stage_ids = stages.sudo()._search(search_domain, order=stages._order)
            # stage_ids = [stage_id for stage_id in stage_ids if stage_id not in [19, 16, 20]]
            stage_ids = [stage_id for stage_id in stage_ids if stage_id not in [(self.env.ref('crm_stage_customization.crm_stage_lang_2').id), (self.env.ref('crm_stage_customization.crm_stage_lang_3').id),
                                                                                (self.env.ref('crm_stage_customization.crm_stage_lang_4').id)]]
            return stages.browse(stage_ids)

    def change_stages_for_lange(self):
        """function for scheduled action to change the
        stage of all previous leads to new stages"""

        target_stage = self.env['crm.lead'].search([('company_id', 'in', [1,2,3,4,5])])
        for lead_stage in target_stage:
            if lead_stage.stage_id.name == "New":
                lead_stage.write({'stage_id': (self.env.ref('crm_stage_customization.crm_stage_lang_2').id)})
            if lead_stage.stage_id.name == "Qualified":
                lead_stage.write({'stage_id': (self.env.ref('crm_stage_customization.crm_stage_lang_3').id)})
            if lead_stage.stage_id.name == "Proposition":
                lead_stage.write({'stage_id': (self.env.ref('crm_stage_customization.crm_stage_lang_4').id)})
