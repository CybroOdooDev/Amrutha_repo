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
    total_amount = fields.Float(string="Amount",
                                help="This field represents the overall amount from which the commission is calculated.")
    total_commission = fields.Float(string="Total Commission",
                                    help="This field represents the calculated commission based on the total amount and applicable percentage.")
    tier = fields.Float(string="Tier")
    commission_to_be_paid = fields.Float(string="Commission Paid",
                                         help="Commission to be paid")
    omissions_insurance = fields.Float(string="Omissions Insurance",
                                       help="Fixed amount based on the total commission received by the company. This amount is subtracted from the agent’s payout before being paid out.")
    is_apply_transaction_coordinator_fee = fields.Boolean(
        string="Apply Transaction Coordinator Fee",
        help="For residential deals, $200 is either subtracted from the agent’s commission if the deal amount is under $125,000, or it’s paid by the brokerage if the deal is $125,000 or above.")
    inside_sale_fee = fields.Float(string="Inside sales fee")
    referral_fee = fields.Float(string="Referral Fee")
    co_agent_fee = fields.Float(string="Co-agent Fee")
    flat_fee = fields.Float(string="Flat Fee",
                            help="Custom flat fee adjustment to the commission.")
    referer_id = fields.Many2one('res.partner', string="External Referral "
                                                       "Agent")
    co_agent_id = fields.Many2one('res.partner', string="Co-Agent ")
    inside_sale_person_id = fields.Many2one('res.users',
                                            string="Inside Sale Person ")
    required_approvers = fields.Many2many('res.users',
                                          string="Required Approvers")
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
        string="Referral rate",
        help="Percentage paid to the referral agent that brought in the lead.",
        default=lambda self: self._default_referral_fee_rate()
    )

    def _default_referral_fee_rate(self):
        # Return the referral_fee_rate from the current company
        return self.env.company.referral_fee_rate

    # Commercial commission plan

    is_calculate_commercial_commission = fields.Boolean(
        string="Compute Commercial Commission",
        help="Enable for Commission calculation.",
        related='company_id.is_calculate_commercial_commission',
        readonly=False,
    )
    total_commercial_commission = fields.Float(string="Total Commission "
                                                      "Received by LRE",
                                               compute="_compute_total_commercial_commission")
    agent_payout_tier = fields.Float(string="Agent Payout Tier",
                                     compute="_compute_agent_payout_tier",
                                     store=True)
    errors_omission_fee = fields.Float(string="Errors & Omission Fee",
                                       compute="_compute_errors_omission_fee",
                                       store=True)
    planned_revenue = fields.Float(string="Amount",
                                   help="This field represents the overall amount from which the commission is calculated.")
    external_referral_fee = fields.Float(string="Referral Fee", readonly=True)
    total_commercial_commission_earned = fields.Float(
        string="Commission earned",
        readonly=True)
    is_sale_lead = fields.Boolean()
    base_rent = fields.Float(
        string="Base Rent",
        help="The base rent amount for the lease.",
    )
    lease_duration = fields.Integer(
        string="Lease Duration (Months)",
        help="The duration of the lease in months.",
    )
    landlord_percentage = fields.Float(
        string="Landlord Percentage (%)",
        help="The percentage of the lease base rent charged to the landlord.",
    )
    commercial_referral_fee_rate = fields.Float(
        string="Referral Fee rate",
        help="Percentage paid to the  referral agent that brought in the "
             "lead.",
        default=lambda self: self._default_commercial_referral_fee_rate()
    )

    def _default_commercial_referral_fee_rate(self):
        # Return the referral_fee_rate from the current company
        return self.env.company.commercial_referral_fee_rate


    @api.onchange('x_studio_opportunity_type_1')
    def _onchange_x_studio_opportunity_type_1(self):
        transaction_type = self.x_studio_opportunity_type_1.x_name
        if transaction_type == 'Sale':
            # Logic for 'sale'
            self.is_sale_lead = True
        else:
            self.is_sale_lead = False

    @api.depends('user_id')
    def _compute_agent_payout_tier(self):
        print("_compute_agent_payout_tier")
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
            print(tier, "tier")
            print(total_previous_year_sales, "total_previous_year_sales")
            if tier:
                lead.agent_payout_tier = tier.commission_percentage / 100.0  # Convert to decimal
            else:
                lead.agent_payout_tier = 0.0  # Default to 0 if no tier is found

    @api.depends('agent_payout_tier', 'planned_revenue')
    def _compute_total_commercial_commission(self):
        """Calculate the total commercial commission for the current lead based on the payout tier."""
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
            if tier:
                lead.agent_payout_tier = tier.commission_percentage / 100.0  # Convert to decimal
            else:
                lead.agent_payout_tier = 0.0  # Default to 0 if no tier is found
            lead.total_commercial_commission = (
                                                       lead.planned_revenue or 0.0) * (
                                                       lead.agent_payout_tier or 0.0)
            transaction_type = lead.x_studio_opportunity_type_1.x_name
            if transaction_type == 'Lease':
                base_rent = lead.base_rent
                lease_duration = lead.lease_duration
                landlord_percentage = lead.landlord_percentage
                if not base_rent or not lease_duration or not landlord_percentage:
                    raise UserError(
                        _("Base Rent, Lease Duration, and Landlord Percentage must be specified for a lease."))
                lead.total_commercial_commission = base_rent * (
                        landlord_percentage / 100)

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
            if transaction_type == 'Sale':
                # Logic for 'sale'
                self.is_sale_lead = True
                self.handle_sale_commission(lead)
            elif transaction_type == 'Lease':
                self.is_sale_lead = False
                # Logic for 'lease'
                self.handle_lease_commission(lead)
            else:
                raise ValueError(
                    "Unknown transaction type: %s" % transaction_type)
            self.generate_pdf_attachment()

    def handle_sale_commission(self, lead):
        print("sale")
        self.external_referral_fee = 0
        if lead.referer_id:  # Check for external referral fee
            external_referral_fee = (
                    lead.total_commercial_commission * (
                    self.commercial_referral_fee_rate or 0.0)
            )
            self.external_referral_fee = external_referral_fee
        total_commercial_commission_earned = (
                lead.total_commercial_commission - lead.errors_omission_fee)
        self.total_commercial_commission_earned = total_commercial_commission_earned
        self.generate_pdf_attachment()

    def handle_lease_commission(self, lead):
        print("Lease")
        tax = self.env['account.tax'].search(
            [('company_id', '=', self.env.company.id),
             ('amount', '=', float(0.00)),
             ('amount_type', '=', 'percent'),
             ('type_tax_use', '=', 'sale'),
             ], limit=1)
        self.external_referral_fee = 0

        base_rent = lead.base_rent
        lease_duration = lead.lease_duration
        landlord_percentage = lead.landlord_percentage
        if not base_rent or not lease_duration or not landlord_percentage:
            raise UserError(
                _("Base Rent, Lease Duration, and Landlord Percentage must be specified for a lease."))
        lead.total_commercial_commission = base_rent * (
                    landlord_percentage / 100)
        print(lead.total_commercial_commission, "total_commercial_commission")
        if lead.referer_id:  # Check for external referral fee
            external_referral_fee = (
                    lead.total_commercial_commission * (
                    self.commercial_referral_fee_rate or 0.0)
            )
            self.external_referral_fee = external_referral_fee
        total_commercial_commission_earned = (
            (lead.total_commercial_commission * lead.agent_payout_tier) -
            lead.errors_omission_fee)
        self.total_commercial_commission_earned = total_commercial_commission_earned
        self.generate_pdf_attachment()

    def create_commercial_invoice(self):
        print("invoice")
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
                    'ref':self.x_studio_property_address,
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

    @api.onchange('omissions_insurance')
    def _onchange_omissions_insurance(self):
        self.is_manual_omissions_insurance = True
        self.compute_commission()

    @api.onchange('is_apply_transaction_coordinator_fee')
    def _onchange_is_apply_transaction_coordinator_fee(self):
        self.is_manual_tc_fee = True
        self.compute_commission()

    @api.onchange('inside_sale_fee')
    def _onchange_inside_sale_fee(self):
        self.is_manual_inside_sale_fee = True
        self.compute_commission()

    @api.onchange('referral_fee')
    def _onchange_referral_fee(self):
        self.is_manual_referral_fee = True
        self.compute_commission()

    @api.onchange('co_agent_fee')
    def _onchange_co_agent_fee(self):
        self.is_manual_co_agent_fee = True
        self.compute_commission()

    @api.onchange('flat_fee')
    def _onchange_flat_fee(self):
        self.is_manual_flat_fee = True
        self.compute_commission()

    # Modify the commission calculation method
    def compute_commission(self):
        if self.stage_id.is_won:
            last_year_date = datetime.now() - timedelta(days=365)

            # Get the partner associated with the user
            if self.user_id.secondary_related_partner_id:
                partner = self.user_id.secondary_related_partner_id
            else:
                partner = self.user_id.partner_id

            # Check if the user belongs to a sales team
            sales_team = self.env['crm.team'].search([
                ('crm_team_member_ids', 'in', self.user_id.id)
            ], limit=1)

            if sales_team:
                # Get all members of the sales team
                team_members = sales_team.crm_team_member_ids
                total_amount_past_year = 0.0

                for member in team_members:
                    partner = member.partner_id or member.secondary_related_partner_id
                    if not partner:
                        continue

                    # Search for account.move.line related to the team member
                    product = self.env['product.product'].search(
                        [('name', '=', 'Commission'),
                         ('default_code', '=', 'COMMISSION')], limit=1)

                    if product:
                        payments = self.env['account.move.line'].search([
                            ('product_id', '=', product.id),
                            ('move_id.move_type', '=', 'in_invoice'),
                            ('move_id.partner_id', '=', partner.id),
                            ('create_date', '>=', last_year_date),
                            ('move_id.state', '=', 'posted')
                        ])
                        total_amount_past_year += sum(
                            payment.price_total for payment in payments)
            else:
                # Individual calculation if the user does not belong to a sales team
                product = self.env['product.product'].search(
                    [('name', '=', 'Commission'),
                     ('default_code', '=', 'COMMISSION')], limit=1)

                if product:
                    payments = self.env['account.move.line'].search([
                        ('product_id', '=', product.id),
                        ('move_id.move_type', '=', 'in_invoice'),
                        ('move_id.partner_id', '=', partner.id),
                        ('create_date', '>=', last_year_date),
                        ('move_id.state', '=', 'posted')
                    ])
                    total_amount_past_year = sum(
                        payment.price_total for payment in payments)

            # Calculate the commission rate based on the total
            commission_rate = self.get_commission_rate(total_amount_past_year)
            self.total_commission = self.total_amount * commission_rate

            # E&O Insurance calculation (skip if manually set)
            if not self.is_manual_omissions_insurance:
                eo_insurance = self.env['eo.insurance'].search([
                    ('from_amount', '<=', self.total_commission),
                    ('to_amount', '>=', self.total_commission),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
                self.omissions_insurance = eo_insurance.eo_to_charge if eo_insurance else 0

            self.commission_to_be_paid = self.total_commission - self.omissions_insurance

            # Transaction Coordinator Fee (skip if manually set)
            if not self.is_manual_tc_fee:
                if self.company_id.is_tc_enabled and self.total_amount < self.company_id.tc_threshold:
                    self.is_apply_transaction_coordinator_fee = True
                    self.commission_to_be_paid -= self.company_id.tc_fee

            else:
                if self.is_apply_transaction_coordinator_fee:
                    self.commission_to_be_paid += self.company_id.tc_fee
                    self.is_apply_transaction_coordinator_fee = False
                else:
                    self.commission_to_be_paid -= self.company_id.tc_fee
                    self.is_apply_transaction_coordinator_fee = False

            # Inside Sales Fee (skip if manually set)
            if not self.is_manual_inside_sale_fee and self.company_id.inside_sale_fee and self.inside_sale_person_id:
                self.inside_sale_fee = self.company_id.inside_sale_fee

            # Referral Fee (skip if manually set)
            if not self.is_manual_referral_fee and self.referral_fee_rate and self.referer_id:
                self.referral_fee = self.total_commission * (
                        self.referral_fee_rate / 100)

            # Coagent Fee (skip if manually set)
            if not self.is_manual_referral_fee and self.company_id.co_agent_fee_rate and self.co_agent_id:
                self.co_agent_fee = self.total_commission * (
                        self.company_id.co_agent_fee_rate / 100)

            if self.inside_sale_fee:
                self.commission_to_be_paid -= self.inside_sale_fee

            if self.referral_fee:
                self.commission_to_be_paid -= self.referral_fee

            if self.co_agent_fee:
                self.commission_to_be_paid -= self.co_agent_fee

            # Flat Fee (skip if manually set)
            if self.flat_fee:
                self.commission_to_be_paid -= self.flat_fee

            # pdf attachment creation
            self.generate_pdf_attachment()
            # self._create_approvals()

    def generate_pdf_attachment(self):
        # Use the report rendering method to generate the PDF
        pdf_content, _ = self.env["ir.actions.report"].sudo()._render_qweb_pdf(
            self.env.ref('commission_plan.action_report_crm_lead'),
            self.id)
        # Generate a unique attachment name
        attachment_name = "Commission Report - %s.pdf" % time.strftime(
            '%Y-%m-%d - %H:%M:%S')
        print(base64.b64encode(pdf_content), "base64.b64encode(pdf_content)")
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

    def action_commission(self):
        """ Action to calculate commission manually """

        self.compute_commission()
        # pdf attachment creation
        self.generate_pdf_attachment()

    def get_commission_rate(self, total_amount):
        """Fetch the correct commission rate based on total amount from tier.tier,
        and enforce minimum commission percentage for the salesperson."""

        tiers = self.env['tier.tier'].search(
            [('company_id', '=', self.company_id.id)], order='amount asc')

        # Default commission rate from tiers
        commission_rate = 0.0
        for tier in tiers:
            if total_amount >= tier.amount:
                commission_rate = tier.commission_percentage / 100.0
                self.tier = tier.commission_percentage

        # Enforce minimum commission rate for the salesperson
        min_commission_percentage = self.user_id.min_commission_percentage or 0.0  # Assume 0.0 if not set
        min_commission_rate = min_commission_percentage / 100.0

        if commission_rate < min_commission_rate:
            commission_rate = min_commission_rate
            self.tier = min_commission_percentage  # Update tier to reflect the enforced minimum

        return commission_rate
