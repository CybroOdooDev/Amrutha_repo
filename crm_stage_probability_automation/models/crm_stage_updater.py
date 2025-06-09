# from odoo import models, api
#
# class CRMStageUpdater(models.TransientModel):
#     _name = 'crm.stage.updater'  # Can be anything
#
#     @api.model
#     def update_crm_stages_for_lang_real_estate(self):
#         print("hookk")
#         company = self.env['res.company'].search([('name', '=', 'Lang Real Estate')], limit=1)
#         if not company:
#             return
#
#         updates = {
#             'New': 'Cold',
#             'Qualified': 'Warm',
#             'Proposition': 'Hot',
#             'Won': 'Won',
#         }
#
#         for old_name, new_name in updates.items():
#             stage = self.env['crm.stage'].search([
#                 ('name', '=', old_name),
#                 ('company_id', '=', False)  # only update global stages or update to target company
#             ], limit=1)
#
#             if stage:
#                 stage.write({
#                     'name': new_name,
#                     'company_id': company.id
#                 })
