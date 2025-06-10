# -*- coding: utf-8 -*-

from odoo import models, fields

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'


    incentive_ids = fields.Many2many(
        'incentives.selection',
        string='Incentives'
    )
