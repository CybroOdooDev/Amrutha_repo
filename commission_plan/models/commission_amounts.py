# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CommissionAmount(models.Model):
    _name = "commission.amount"
    _description = "Commission Amount"

    user_id = fields.Many2one('res.users',string="Sales Person")
    commission_id = fields.Many2one('commission.plan',
                                         string="Commission Plan")
    amount = fields.Float(required=True, default=0.0, tracking=True)