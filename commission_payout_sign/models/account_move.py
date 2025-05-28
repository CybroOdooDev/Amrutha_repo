from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    crm_lead_id =  fields.Many2one('crm.lead',string="Lead")