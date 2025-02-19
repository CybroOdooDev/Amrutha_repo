# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_calculate_commission = fields.Boolean(
        string="Compute Commission",
        help="Enable for Commission calculation.",
    )
    tc_fee = fields.Float(
        string="Transaction Coordinator Fee",
        default=200,
        help="Fee charged for deals under the threshold amount.",
    )
    tc_threshold = fields.Float(
        string="Transaction Threshold",
        default=125000,
        help="Threshold for the Transaction Coordinator Fee.",
    )
    is_tc_enabled = fields.Boolean(
        string="Enable Transaction Coordinator Fee",
        help="Enable or disable the transaction coordinator fee calculation.",
    )
    inside_sale_fee = fields.Float(
        string="Inside Sales Fee",
        default=250,
        help="Amount paid to the inside salesperson that brought in the lead.",
    )
    referral_fee_rate=fields.Float(
        string="Referral Fee rate",
        default=25,
        help="Amount paid to the inside salesperson that brought in the lead.",
    )
    co_agent_fee_rate = fields.Float(
        string="Co-agent Fee rate",
        default=25,
    )
    is_calculate_commercial_commission = fields.Boolean(
        string="Compute Commercial Commission",
        help="Enable for Commercial Commission calculation.",
    )
    commercial_referral_fee_rate = fields.Float(
        string="Referral Fee rate",
        default=25,
        help="Amount paid to the inside salesperson that brought in the lead.",
    )
