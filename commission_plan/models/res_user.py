from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    min_commission_percentage = fields.Float(
        string="Minimum Commission Percentage",
        help="The minimum commission percentage applicable to this salesperson."
    )
    has_minimum_commission = fields.Boolean(string="2,000/4,000 minimums")