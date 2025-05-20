# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CommissionTier(models.Model):
    _name = "tier.tier"
    _description = "Tiers"
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )
    amount = fields.Float(
        required=True, string="Amount", help="Amount limit"
    )
    commission_percentage = fields.Float(
        required=True, string="Commission Percentage",
        help="Percentage that given as commission"
    )
    commission_id = fields.Many2one('commission.plan',
                                    hlep="Associated commission plan")
