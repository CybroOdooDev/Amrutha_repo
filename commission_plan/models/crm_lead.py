# -*- coding: utf-8 -*-
import base64

from odoo import fields, models, api, _, Command
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
import time
from datetime import date


class Lead(models.Model):
    _inherit = 'crm.lead'

    is_calculate_commission = fields.Boolean(
        string="Compute Commission",
        help="Enable for Commission calculation.",
        related='company_id.is_calculate_commission',
        readonly=False,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', readonly=True)
    _is_applicable_for_commission = fields.Boolean(
        string="Is applicable for Commission")
    total_amount = fields.Float(string="Total Commission Received by LRE",
                                help="This field represents the overall amount from which the commission is calculated.")
    total_commission = fields.Float(string="Total Commission Earned by Agent",
                                    help="This field represents the "
                                         "calculated commission based on the total amount and applicable percentage.",
                                    readonly=True)
    tier = fields.Float(string="Tier", compute="_compute_tier",
                        store=True)
    commission_to_be_paid = fields.Float(string="Commission Paid",
                                         help="Commission to be paid")
    omissions_insurance = fields.Float(string="Omissions Insurance",
                                       help="Fixed amount based on the total commission received by the company. This amount is subtracted from the agent’s payout before being paid out.")
    is_apply_transaction_coordinator_fee = fields.Boolean(
        string="Apply Transaction Coordinator Fee",
        help="For residential deals, $200 is either subtracted from the agent’s commission if the deal amount is under $125,000, or it’s paid by the brokerage if the deal is $125,000 or above.")
    transaction_coordinator_fee = fields.Float(
        string="Transaction Coordinator Fee")
    inside_sale_fee = fields.Float(string="Signage Fee")
    referral_fee = fields.Float(string="Internal Referral Fee")
    co_agent_fee = fields.Float(string="Co-agent Fee")
    flat_fee = fields.Float(string="Other Fees",
                            help="Custom flat fee adjustment to the commission.")
    referer_id = fields.Many2one('res.partner', string="External Referral "
                                                       "Agent")
    co_agent_id = fields.Many2one('res.partner', string="Co-Agent ")
    co_agent_user_id = fields.Many2one('res.users', string="Co-Agent User")
    inside_sale_person_id = fields.Many2one('res.users',
                                            string="Inside Sale Person ")
    required_approvers = fields.Many2many('res.users',
                                          string="Required Approvers", default=lambda self: self._get_default_approvers())
    is_manual_omissions_insurance = fields.Boolean(
        string="Manual Omissions Insurance",
        help="Indicates if omissions insurance was manually set.")
    is_manual_tc_fee = fields.Boolean(
        string="Manual Transaction Coordinator Fee",
        help="Indicates if transaction coordinator fee was manually set.")
    is_manual_inside_sale_fee = fields.Boolean(
        string="Manual Inside Sales Fee",
        help="Indicates if inside sales fee was manually set.")
    is_manual_referral_fee = fields.Boolean(string="Manual Referral Fee",
                                            help="Indicates if referral fee was manually set.")
    is_manual_co_agent_fee = fields.Boolean(string="Manual Co-Agent Fee",
                                            help="Indicates if Co-agent fee "
                                                 "was manually set.")
    is_manual_flat_fee = fields.Boolean(string="Manual Flat Fee",
                                        help="Indicates if flat fee was manually set.")
    commission_attachment_id = fields.Many2one('ir.attachment',
                                               string="Attachments",
                                               help="Add attachment file")
    pdf_report = fields.Binary('PDF')

    referral_fee_rate = fields.Float(
        string="External Referral rate",
        help="Percentage paid to the referral agent that brought in the lead."
    )
    total_sales_price = fields.Float(string="Total Sales Price",
                                     help="Total Sales price")
    total_list_price = fields.Float(string="List Price",
                                    help="Total List price")
    minimum_commission_due = fields.Float(string="Minimum Commission Due",
                                          compute="_compute_minimum_commission_due",
                                          store=True)
    commission_to_be_converted_by_agent = fields.Float(string="Commission to "
                                                              "be covered by "
                                                              "Agent",
                                                       compute="_compute_commission_to_be_converted_by_agent",
                                                       store=True)
    mentor_fee = fields.Float(string="Mentor Fee")
    agent_pass_thru_income = fields.Float(string="Agent Pass Thru Income")
    co_agent_percentage = fields.Float(string="Co-Agent Percentage",
                                       default=30.0)
    residential_external_referral_fee = fields.Float(string="External "
                                                            "Referral Fee",
                                                     compute="_compute_residential_external_referral_fee",
                                                     store=True)
    total_received_by_lre = fields.Float(
        string="Total Received by Lange Real Estate",
        compute="_compute_total_received_by_lre",
        store=True)
    residential_commission_earned = fields.Float(string="Commission Earned",
                                                 compute="_compute_residential_commission_earned",
                                                 store=True)
    co_agent_commission = fields.Float(string="Co-Agent Commission",
                                       compute="_compute_co_agent_commission",
                                       store=True)
    payable_to_agent = fields.Float(string="Payable to Agent",
                                    compute="_compute_payable_to_agent",
                                    store=True)
    payable_to_co_agent = fields.Float(string="Payable to Co-Agent",
                                       compute="_compute_payable_to_co_agent",
                                       store=True)
    company_id = fields.Many2one('res.company',  default=lambda self: self.env.company)
    company_check = fields.Char(compute="_compute_check_company")
    lead_source = fields.Selection([('after hours', 'After Hours'), ('brokerage call', 'Brokerage Call'), ('broker', 'Broker'), ('cold calls', 'Cold Calls'),
                                    ('derby movie theater', 'Derby Movie Theater'), ('development deals', 'Development Deals'), ('family/friend', 'Family/Friend'),
                                    ('FSBO lead', 'FSBO Lead'), ('ihomefinder', 'ihomefinder'), ('inside sales networking', 'Inside Sales Networking'),
                                    ('LANGE affiliate company', 'LANGE Affiliate Company (TCRS, JBL, etc.)'), ('LANGE employee program', 'LANGE Employee Program'), ('lead generation paid by agent', 'Lead Generation Paid By Agent (Zillow.com, realtor.com, etc)'),
                                    ('lre event lead form', 'LRE Event Lead Form'), ('open house', 'Open House'), ('past client', 'Past Client'), ('personal contact', 'Personal Contact'),
                                    ('personal transaction', 'Personal Transaction'), ('realtor.com', 'Realtor.com (Paid By Brokerage)'), ('referral', 'Referral'),
                                    ('registered bidder', 'Registered Bidder - Auction'), ('signage', 'Signage'), ('social media', 'Social Media'),
                                    ('website chat', 'Website Chat'), ('website email', 'Website Email'), ('zillow.com', 'Zillow.com (Paid By Brokerage)'), ('google', 'Google'), ('hero program', 'Hero Program'), ('teacher program', 'Teacher Program'), ('billboard', 'Billboard'), ('chamber/networking group', 'Chamber/Networking Group'), ('development call', 'Development Call')], string='Lead Source')
    lead_classification = fields.Selection([('exponential', 'Exponential'), ('agent sourced', 'Agent Sourced')], string='Lead Classification')
    override_minimum_commission = fields.Boolean(string="Override Minimum Commission")
    co_agent_payout = fields.Float(string="Co Agent Payout", compute="_compute_co_agent_payout")
    seller_attn = fields.Char(string="Attn")
    seller_address = fields.Char(string="Address")
    buyer_attn = fields.Char(string="Attn")
    buyer_address = fields.Char(string="Address")
    brokerage_name = fields.Char(string="Brokerage Name")
    brokerage_address = fields.Char(string="Brokerage Address")
    buyer_brokerage_name = fields.Char(string="Brokerage Name")
    buyer_brokerage_address = fields.Char(string="Brokerage Address")

    @api.depends('minimum_commission_due', 'referral_fee_rate')
    def _compute_residential_external_referral_fee(self):
        for lead in self:
            lead.residential_external_referral_fee = (
                    lead.minimum_commission_due *
                    (
                            lead.referral_fee_rate / 100))

    @api.depends('total_amount', 'commission_to_be_converted_by_agent',
                 'residential_external_referral_fee',
                 'residential_external_referral_fee', 'agent_pass_thru_income')
    def _compute_total_received_by_lre(self):
        for lead in self:
            total = (lead.total_amount +
                     lead.commission_to_be_converted_by_agent) - lead.residential_external_referral_fee
            lead.total_received_by_lre = (
                                             lead.residential_external_referral_fee) + total + lead.agent_pass_thru_income

    @api.depends('total_amount', 'commission_to_be_converted_by_agent',
                 'residential_external_referral_fee')
    def _compute_residential_commission_earned(self):
        for lead in self:
            total = (lead.total_amount +
                     lead.commission_to_be_converted_by_agent) - lead.residential_external_referral_fee
            lead.residential_commission_earned = total * (lead.tier/100)

    @api.depends('total_amount', 'commission_to_be_converted_by_agent',
                 'residential_external_referral_fee', 'co_agent_percentage')
    def _compute_co_agent_commission(self):
        for lead in self:
            total = (lead.total_amount +
                     lead.commission_to_be_converted_by_agent) - lead.residential_external_referral_fee
            lead.co_agent_commission = total * (lead.co_agent_percentage / 100)

    @api.depends('residential_commission_earned', 'agent_pass_thru_income',
                 'minimum_commission_due',
                 'transaction_coordinator_fee', 'referral_fee',
                 'inside_sale_fee', 'mentor_fee', 'flat_fee')
    def _compute_payable_to_agent(self):
        for lead in self:
            lead.payable_to_agent = ((lead.residential_commission_earned +
                                      lead.agent_pass_thru_income) - lead.co_agent_commission -
                                     lead.commission_to_be_converted_by_agent - lead.transaction_coordinator_fee - lead.referral_fee - lead.inside_sale_fee - lead.mentor_fee - lead.flat_fee)

    @api.depends('co_agent_commission','referral_fee','mentor_fee')
    def _compute_payable_to_co_agent(self):
        for lead in self:
            lead.payable_to_co_agent = (lead.co_agent_commission +
                                        lead.referral_fee + lead.mentor_fee)

    def action_commission(self):
        """ Action to calculate commission manually """
        self._compute_tier()
        self._compute_residential_external_referral_fee()
        self._compute_total_received_by_lre()
        self._compute_residential_commission_earned()
        self._compute_co_agent_commission()
        self._compute_payable_to_agent()
        self._compute_payable_to_co_agent()
        # pdf attachment creation
        self.generate_pdf_attachment()

    # Commercial commission plan

    is_calculate_commercial_commission = fields.Boolean(
        string="Compute Commercial Commission",
        help="Enable for Commission calculation.",
        related='company_id.is_calculate_commercial_commission',
        readonly=False,
    )
    total_commercial_commission = fields.Float(string="Commission Earned by Agent",
                                               compute="_compute_total_commercial_commission")
    agent_payout_tier = fields.Float(string="Agent Payout Tier",
                                     compute="_compute_agent_payout_tier",
                                     )
    errors_omission_fee = fields.Float(string="Errors & Omission Fee",
                                       compute="_compute_errors_omission_fee",
                                       store=True)
    planned_revenue = fields.Float(string="Total Commission Received by LRE",
                                   help="This field represents the overall amount from which the commission is calculated.")
    external_referral_fee = fields.Float(string="External Referral Fee", readonly=True,  compute='_compute_external_referral_fee')
    total_commercial_commission_earned = fields.Float(
        string="Commission earned",
        readonly=True)
    is_sale_lead = fields.Boolean()
    is_lease_lead = fields.Boolean()
    is_not_commercial_lead = fields.Boolean()
    is_not_residential_lead = fields.Boolean()
    is_company_allowed = fields.Boolean()
    find_company_lange = fields.Boolean()
    is_company_commercial = fields.Boolean()
    base_rent = fields.Float(
        string="Base Rent",
        help="The base rent amount for the lease.",
    )
    lease_duration = fields.Integer(
        string="Lease Duration (Months)",
        help="The duration of the lease in months.",
    )
    landlord_percentage = fields.Float(
        string="Agent Commission % Charged",
        help="The percentage of the lease base rent charged to the landlord.",
    )
    commercial_referral_fee_rate = fields.Float(
        string="External Referral rate",
        help="Percentage paid to the  referral agent that brought in the "
             "lead.")
    # Add these new fields to the Lead class in crm_lead.py
    external_marketing_agency = fields.Many2one('res.partner',
                                                string="External Marketing "
                                                       "Agency")
    marketing_fee = fields.Float(string="Marketing Fee")
    co_agent_percentage = fields.Float(string="Co-Agent Percentage")  # This already exists, just noting it's used
    is_manual_marketing_fee = fields.Boolean(string="Manual Marketing Fee")
    # New fields for commercial commission calculations
    balance_for_distribution = fields.Float(
        string="Balance for Distribution",
        compute="_compute_balance_for_distribution")
    commercial_co_agent_commission = fields.Float(
        string="Commercial Co-Agent Commission",
        compute="_compute_commercial_co_agent_commission",
        store=True)
    commercial_payable_to_agent = fields.Float(
        string="Commercial Payable to Agent",
        compute="_compute_commercial_payable_to_agent",
        store=True)
    commercial_payable_to_co_agent = fields.Float(
        string="Commercial Payable to Co-Agent",
        compute="_compute_commercial_payable_to_co_agent",
        store=True)
    eo_insurance_agent_portion = fields.Float(
        string="E&O Insurance (Agent Portion)",
        compute="_compute_eo_insurance_portions",
        store=True)
    eo_insurance_co_agent_portion = fields.Float(
        string="E&O Insurance (Co-Agent Portion)",
        compute="_compute_eo_insurance_portions",
        store=True)
    lease_commencement_date = fields.Date(string="Lease Commencement")

    # --------------------------
    # Computation Methods
    # --------------------------

    @api.depends('planned_revenue',
                 'external_referral_fee', 'marketing_fee', 'base_rent', 'landlord_percentage')
    def _compute_balance_for_distribution(self):
        for lead in self:
            if lead.x_studio_opportunity_type_1.x_name == "Commercial Lease":
                lead.balance_for_distribution = ((lead.base_rent * lead.landlord_percentage / 100)
                                                 - lead.external_referral_fee)
            else:
                lead.balance_for_distribution = (
                        lead.planned_revenue
                        - lead.marketing_fee
                        - lead.external_referral_fee
                )

    @api.depends('balance_for_distribution', 'co_agent_percentage')
    def _compute_commercial_co_agent_commission(self):
        for lead in self:
            lead.commercial_co_agent_commission = (
                    lead.balance_for_distribution * (
                        lead.co_agent_percentage / 100)
            )

    @api.depends('errors_omission_fee', 'co_agent_percentage')
    def _compute_eo_insurance_portions(self):
        for lead in self:
            total_eo = lead.errors_omission_fee
            co_agent_percent = lead.co_agent_percentage / 100
            if co_agent_percent != 0:
                lead.eo_insurance_co_agent_portion = total_eo * co_agent_percent
                lead.eo_insurance_agent_portion = total_eo * (1 - co_agent_percent)
            else:
                lead.eo_insurance_agent_portion = total_eo
                lead.eo_insurance_co_agent_portion = 0.0


    @api.depends('balance_for_distribution', 'agent_payout_tier',
                 'eo_insurance_agent_portion',
                 'commercial_co_agent_commission',
                 'transaction_coordinator_fee','referral_fee', 'flat_fee')
    def _compute_commercial_payable_to_agent(self):
        for lead in self:
            lead.commercial_payable_to_agent = (
                    lead.total_commercial_commission
                    - lead.eo_insurance_agent_portion
                    - lead.commercial_co_agent_commission
                    - lead.transaction_coordinator_fee
                    - lead.referral_fee
                    - lead.flat_fee
            )

    @api.depends('commercial_co_agent_commission',
                 'eo_insurance_co_agent_portion',
                 'referral_fee')
    def _compute_commercial_payable_to_co_agent(self):
        for lead in self:
            lead.commercial_payable_to_co_agent = (
                    lead.commercial_co_agent_commission
                    - lead.eo_insurance_co_agent_portion
                    + lead.referral_fee
            )

    @api.depends('minimum_commission_due', 'total_amount')
    def _compute_commission_to_be_converted_by_agent(self):
        for lead in self:
            if lead.total_amount < lead.minimum_commission_due:
                lead.commission_to_be_converted_by_agent = (
                        lead.minimum_commission_due - lead.total_amount)
            else:
                lead.commission_to_be_converted_by_agent = 0.0

    @api.depends('total_sales_price', 'x_studio_opportunity_type_1')
    def _compute_minimum_commission_due(self):
        for lead in self:
            lead.minimum_commission_due = 0.0
            if lead.total_sales_price:
                if lead.user_id.has_minimum_commission:
                    opportunity_type = lead.x_studio_opportunity_type_1.x_name if lead.x_studio_opportunity_type_1 else False
                    if opportunity_type == 'Residential Buy' and lead.total_sales_price <= 67000:
                        lead.minimum_commission_due = 2000.0
                    elif opportunity_type == 'Residential Sale' and lead.total_sales_price <= 134000:
                        lead.minimum_commission_due = 4000.0
                    else:
                        # Fall back to 3% calculation if conditions aren't met
                        lead.minimum_commission_due = lead.total_sales_price * (
                                3 / 100)
                else:
                    # Original 3% calculation if the user doesn't have the minimum commission option
                    lead.minimum_commission_due = lead.total_sales_price * (
                            3 / 100)

    @api.depends('total_amount')
    def _compute_tier(self):
        """
        Calculate the current payout percentage based on the agent's past year payments and tiers.

        Steps:
        1. Find the Commission product
        2. Get all payments to this agent in the past year
        3. Sum the total amount paid
        4. Determine commission rate based on tier thresholds

        Returns:
            float: The current payout percentage (e.g., 10.0 for 10%)
        """

        # Find the product for Commission
        product = self.env['product.product'].search(
            [('name', '=', 'Commission'),
             ('default_code', '=', 'COMMISSION')], limit=1)
        if not product:
            return 0.0  # If no Commission product is found, return 0%

        # Calculate the date for one year ago
        last_year_date = datetime.now() - timedelta(days=365)
        # Search for payments in the past year
        payments = self.env['account.move.line'].search([
            ('product_id', '=', product.id),
            ('move_id.move_type', '=', 'in_invoice'),
            ('move_id.partner_id', '=',
             self.env.user.secondary_related_partner_id.id
             if self.env.user.secondary_related_partner_id else
             self.env.user.partner_id.id),
            ('create_date', '>=', last_year_date),
            ('move_id.state', '=', 'posted')
        ])
        # Calculate the total amount paid in the past year
        total_amount_past_year = sum(
            payment.price_total for payment in payments)

        # Search for tiers in ascending order of amount
        tiers = self.env['tier.tier'].search(
            [('company_id', '=', self.env.company.id)], order='amount asc')

        # Determine the commission rate based on tiers
        commission_rate = 0.0
        for tier in tiers:
            if total_amount_past_year >= tier.amount:
                commission_rate = tier.commission_percentage / 100.0
                self.tier = commission_rate *100  # Update tier to reflect the
                # enforced minimum

            else:
                self.tier = self.env.user.min_commission_percentage

    @api.onchange('x_studio_opportunity_type_1')
    def _onchange_lease_x_studio_opportunity_type_1(self):
        transaction_type = self.x_studio_opportunity_type_1.x_name
        self.is_lease_lead = False
        self.is_not_commercial_lead = False
        self.is_sale_lead = False
        self.is_not_residential_lead = False

        if transaction_type == 'Commercial Lease':
            self.is_lease_lead = True
        if transaction_type in ('Residential', 'Personal Property'):
            self.is_not_commercial_lead = True
        if transaction_type in ('Personal Property', 'Commercial'):
            self.is_not_residential_lead = True
        else:
            self.is_sale_lead = True

    @api.depends('user_id')
    def _compute_agent_payout_tier(self):
        """Compute the Agent Payout Tier dynamically using tier.tier."""
        for lead in self:
            if not lead.user_id:
                lead.agent_payout_tier = 0.0
                continue

            # Fetch previous year
            today = date.today()
            last_year_start = date(today.year - 1, 1, 1)
            last_year_end = date(today.year - 1, 12, 31)

            # Get all leads won by the agent (user_id) in the previous year
            previous_year_leads = self.env['crm.lead'].search([
                ('user_id', '=', lead.user_id.id),
                ('date_closed', '>=', last_year_start),
                ('date_closed', '<=', last_year_end),
                ('stage_id.is_won', '=', True),
                # Only include "won" opportunities
            ])
            total_previous_year_sales = sum(
                previous_year_leads.mapped('planned_revenue'))

            # Fetch the correct tier for the total sales
            tier = self.env['tier.tier'].search([
                ('company_id', '=', lead.company_id.id),
                ('amount', '<=', total_previous_year_sales)
            ], order='amount desc', limit=1)
            if not tier:
                # If no tier found (sales < all tier amounts), get the tier with minimum amount
                tier = self.env['tier.tier'].search([
                    ('company_id', '=', lead.company_id.id)
                ], order='amount asc', limit=1)
            if tier:
                lead.agent_payout_tier = tier.commission_percentage / 100.0  # Convert to decimal
            else:
                lead.agent_payout_tier = 0.0  # Default to 0 if no tier is found

    @api.depends('agent_payout_tier', 'balance_for_distribution')
    def _compute_total_commercial_commission(self):
        """Calculate the total commercial commission for the current lead based on the payout tier."""
        for lead in self:
            lead.total_commercial_commission = ((lead.balance_for_distribution or 0.0) * (100 - lead.co_agent_percentage))/100 * (lead.agent_payout_tier or 0.0)

    @api.depends('total_commercial_commission')
    def _compute_errors_omission_fee(self):
        """Compute the Errors & Omission Fee dynamically from the eo.insurance model."""
        for lead in self:
            eo_insurance = self.env['eo.insurance'].search([
                ('company_id', '=', lead.company_id.id),
                ('from_amount', '<=', lead.total_commercial_commission),
                ('to_amount', '>=', lead.total_commercial_commission)
            ], limit=1)

            if eo_insurance:
                lead.errors_omission_fee = eo_insurance.eo_to_charge
            else:
                lead.errors_omission_fee = 0.0  # Default to 0 if no matching range is found

    def action_commercial_commission(self):
        for lead in self:
            transaction_type = lead.x_studio_opportunity_type_1.x_name
            if transaction_type == 'Commercial Sale':
                lead.is_sale_lead = True
                self.handle_sale_commission(lead)
            elif transaction_type == 'Commercial Lease':
                lead.is_sale_lead = False
                self.handle_lease_commission(lead)
            elif transaction_type == 'Commercial':
                self.handle_lease_commission(lead)
            else:
                raise ValidationError(
                    "Unknown transaction type: %s" % transaction_type)

            # Compute all commercial related fields
            lead._compute_agent_payout_tier()
            lead._compute_balance_for_distribution()
            lead._compute_commercial_co_agent_commission()
            lead._compute_eo_insurance_portions()
            lead._compute_commercial_payable_to_agent()
            lead._compute_commercial_payable_to_co_agent()
            lead.generate_pdf_attachment()

            self.generate_pdf_attachment()

    def handle_sale_commission(self, lead):
        lead.external_referral_fee = 0
        if lead.referer_id:
            lead.external_referral_fee = (
                    lead.total_commercial_commission *
                    (lead.commercial_referral_fee_rate / 100)
            )
        lead.total_commercial_commission_earned = (
                lead.total_commercial_commission - lead.errors_omission_fee
        )

    def handle_lease_commission(self, lead):

        lead.total_commercial_commission = lead.base_rent * (
                    lead.landlord_percentage / 100)
        lead.external_referral_fee = 0

        if lead.referer_id:
            lead.external_referral_fee = (
                    lead.total_commercial_commission *
                    (lead.commercial_referral_fee_rate / 100)
            )

        lead.total_commercial_commission_earned = (
                (lead.total_commercial_commission * lead.agent_payout_tier) -
                lead.errors_omission_fee
        )

    def create_commercial_invoice(self):
        tax = self.env['account.tax'].search(
            [('company_id', '=', self.env.company.id),
             ('amount', '=', float(0.00)),
             ('amount_type', '=', 'percent'),
             ('type_tax_use', '=', 'sale'),
             ], limit=1)
        for lead in self:
            if lead.referer_id:  # Check for external referral fee
                self.env['account.move'].create([{
                    'move_type': 'in_invoice',
                    'partner_id': self.referer_id.id,
                    'crm_lead_id': self.id,
                    'ref': self.x_studio_property_address,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': self.env.ref(
                            'commission_payout_sign.product_referral').id,
                        'price_unit': self.external_referral_fee,
                        'quantity': 1,
                        'tax_ids': [Command.set(tax.ids)]
                    })]
                }])
            self.env['account.move'].create([{
                'move_type': 'in_invoice',
                'partner_id': self.user_id.id,
                'crm_lead_id': self.id,
                'ref': self.x_studio_property_address,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.env.ref(
                        'commission_payout_sign.product_commission').id,
                    'price_unit': self.total_commercial_commission_earned,
                    'quantity': 1,
                    'tax_ids': [Command.set(tax.ids)]
                })]
            }])


    def generate_pdf_attachment(self):
        # Use the report rendering method to generate the PDF
        if self.is_calculate_commission:
            pdf_content, _ = self.env["ir.actions.report"].sudo()._render_qweb_pdf(
                self.env.ref('commission_plan.action_report_crm_lead'),
                self.id)
        if self.x_studio_opportunity_type_1.x_name in ('Commercial Sale', 'Commercial'):
            pdf_content, _ = self.env[
                "ir.actions.report"].sudo()._render_qweb_pdf(
                self.env.ref('commission_plan.action_report_crm_lead_commercial'),
                self.id)
        if self.x_studio_opportunity_type_1.x_name == "Commercial Lease":
            pdf_content, _ = self.env[
                "ir.actions.report"].sudo()._render_qweb_pdf(
                self.env.ref('commission_plan.action_report_crm_lead_lease_payout'),
                self.id)
        # Generate a unique attachment name
        attachment_name = "Commission Report - %s.pdf" % time.strftime(
            '%Y-%m-%d - %H:%M:%S')
        # Create the attachment with the PDF content
        attachment = self.env['ir.attachment'].create({
            'name': attachment_name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content).decode('utf-8'),
            # Odoo expects base64 encoded binary data
            'mimetype': 'application/x-pdf',
            'res_model': self._name,
            # Link the attachment to this record's model
            'res_id': self.id,  # Link the attachment to this specific record
        })
        self.commission_attachment_id = attachment.id
        self.pdf_report = self.commission_attachment_id.datas

    @api.depends('external_referral_fee', 'planned_revenue', 'base_rent',
                 'landlord_percentage' )
    def _compute_external_referral_fee(self):
        """ Compute the external refferal fee based on amount
        received times the referral rate"""
        for lead in self:
            if lead.x_studio_opportunity_type_1.x_name == "Commercial Lease":
                lead.external_referral_fee =( ((lead.base_rent * lead.landlord_percentage)/100) * lead.commercial_referral_fee_rate) / 100
            else:
                lead.external_referral_fee = lead.planned_revenue * (lead.commercial_referral_fee_rate / 100)

    @api.depends('company_id')
    def _compute_check_company(self):
        """Function to find the current company is Auctions,
         Residential, or Commercial"""
        self.company_check = False

        if self.env.company.id in [4,3,2]:
            self.is_company_allowed = True
        if self.env.company.id in [1,2,3,4,5]:
            self.find_company_lange = True
        if self.env.company.id == 3:
            self.is_company_commercial = True

    @api.onchange('override_minimum_commission')
    def _onchange_override_minimum_commission(self):
        """allow users to override the minimum commission due"""

        if self.override_minimum_commission == True:
            self.minimum_commission_due = 0.0

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        active_company = self.env.company
        if view_type == 'form' and active_company.id in [1, 2, 3, 4, 5]:
            for node in arch.xpath("//field[@name='expected_revenue']"):
                node.set('string', 'Expected Commission')

        if view_type == 'list' and active_company.id in [1, 2, 3, 4, 5]:
            for node in arch.xpath("//field[@name='expected_revenue']"):
                node.set('string', 'Expected Commission')
        return arch, view

    @api.depends('co_agent_percentage', 'balance_for_distribution', 'co_agent_user_id')
    def _compute_co_agent_payout(self):
        """computer co-agent payout using tier as users min_commission_percentage"""
        self.co_agent_payout = 0
        for lead in self:
            lead.co_agent_payout = (((lead.balance_for_distribution or 0.0) * (lead.co_agent_percentage))/100 *
                                    (lead.co_agent_user_id.min_commission_percentage or 0.0)/100)

    @api.model
    def _get_default_approvers(self):
        """set default approvers"""
        if self.env.company.id == 2:
            names = [" Dana Miotto", "Bethany Webster", "Heather Stevenson "]
            approvers = self.env['res.users'].search([('name', 'in', names)]).ids
        else:
            approvers = []
        return approvers
