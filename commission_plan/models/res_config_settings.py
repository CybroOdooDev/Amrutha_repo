# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_calculate_commission = fields.Boolean(
        string="Apply Commission",
        help="Enable for Commission calculation.",
        related='company_id.is_calculate_commission',
        readonly=False,
    )
    tc_fee = fields.Float(
        string="Transaction Coordinator Fee",
        default=200,
        help="Fee charged for deals under the threshold amount.",
        related='company_id.tc_fee',
        readonly=False,

    )
    tc_threshold = fields.Float(
        string="Transaction Threshold",
        default=125000,
        help="Threshold for the Transaction Coordinator Fee.",
        related='company_id.tc_threshold',
        readonly=False,
    )
    is_tc_enabled = fields.Boolean(
        string="Enable Transaction Coordinator Fee",
        help="Enable or disable the transaction coordinator fee calculation.",
        related='company_id.is_tc_enabled',
        readonly=False,
    )
    inside_sale_fee = fields.Float(
        string="Inside Sales Fee",
        default=250,
        help="Amount paid to the inside salesperson that brought in the lead.",
        related='company_id.inside_sale_fee',
        readonly=False,
    )
    referral_fee_rate = fields.Float(
        string="Referral Fee rate",
        default=25,
        help="Amount paid to the inside salesperson that brought in the lead.",
        related='company_id.referral_fee_rate',
        readonly=False,

    )
    co_agent_fee_rate = fields.Float(
        string="Co-agent Fee rate",
        default=25,
        related='company_id.co_agent_fee_rate',
        readonly=False,

    )

    # Commercial Commission

    is_calculate_commercial_commission = fields.Boolean(
        string="Apply Commercial Commission",
        help="Enable for Commercial Commission calculation.",
        related='company_id.is_calculate_commercial_commission',
        readonly=False,
    )
    commercial_referral_fee_rate = fields.Float(
        string="Referral Fee rate",
        default=25,
        help="Amount paid to the inside salesperson that brought in the lead.",
        related='company_id.referral_fee_rate',
        readonly=False,

    )
