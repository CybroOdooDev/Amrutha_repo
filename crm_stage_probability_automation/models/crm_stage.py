from odoo import models, api, fields

class CRMStage(models.Model):
    _inherit = 'crm.stage'

    company_id = fields.Many2one('res.company', string='Company')


