from odoo import models, fields, api, _,Command



class ResUsers(models.Model):
    _inherit = 'res.users'

    secondary_related_partner_id = fields.Many2one('res.partner',
                                                   string="payout partner")
