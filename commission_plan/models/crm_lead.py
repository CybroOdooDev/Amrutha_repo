# -*- coding: utf-8 -*-
import base64

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import time


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
    referer_id = fields.Many2one('res.partner', string="Referrer Person")
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
            if not self.is_manual_referral_fee and self.company_id.referral_fee_rate and self.referer_id:
                self.referral_fee = self.total_commission * (
                        self.company_id.referral_fee_rate / 100)

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
        print(base64.b64encode(pdf_content),"base64.b64encode(pdf_content)")
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
