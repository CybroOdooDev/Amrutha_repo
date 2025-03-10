from datetime import datetime, timedelta
from odoo import models, fields, api


class CRMDashboard(models.Model):
    _inherit = 'crm.lead'
    _description = 'CRM Dashboard Details'


    def get_dashboard_data(self):
        """
        Compute and return dynamic data for the CRM dashboard.
        """

        # Calculate current payout percentage
        current_payout = self.calculate_current_payout_percentage()

        # Calculate Last Twelve Months (LTM) Commissions
        ltm_commissions = self.calculate_ltm_commissions()

        # # Calculate number of deals closing this week
        # closing_this_week = self.calculate_deals_closing_this_week()
        #
        # # Calculate amount expiring this month
        # expiring_this_month = self.calculate_expiring_this_month()
        #
        # # Calculate number of deals closing this month
        # closing_this_month = self.calculate_deals_closing_this_month()

        return {
            'currentPayout': f"{current_payout}%",
            'ltmCommissions': ltm_commissions,
            'closingThisWeek': 4,
            'expiringThisMonth': 5,
            'closingThisMonth': 8,
        }

    def calculate_current_payout_percentage(self):
        """
        Calculate the current payout percentage based on the agent's past year payments and tiers.
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
            ('move_id.partner_id', '=', self.partner_id.id),  # Assuming partner_id is the agent
            ('create_date', '>=', last_year_date),
            ('move_id.state', '=', 'posted')
        ])

        # Calculate the total amount paid in the past year
        total_amount_past_year = sum(payment.price_total for payment in payments)

        # Search for tiers in ascending order of amount
        tiers = self.env['tier.tier'].search(
            [('company_id', '=', self.company_id.id)], order='amount asc')

        # Determine the commission rate based on tiers
        commission_rate = 0.0
        for tier in tiers:
            if total_amount_past_year >= tier.amount:
                commission_rate = tier.commission_percentage / 100.0

        return commission_rate * 100  # Convert to percentage

    def calculate_ltm_commissions(self):
        """
        Calculate the total commissions earned in the last twelve months.
        """
        # Find the product for Commission
        product = self.env['product.product'].search(
            [('name', '=', 'Commission'),
             ('default_code', '=', 'COMMISSION')], limit=1)

        if not product:
            return 0.0  # If no Commission product is found, return 0

        # Calculate the date for one year ago
        last_year_date = datetime.now() - timedelta(days=365)

        # Search for payments in the past year
        payments = self.env['account.move.line'].search([
            ('product_id', '=', product.id),
            ('move_id.move_type', '=', 'in_invoice'),
            ('move_id.partner_id', '=', self.partner_id.id),  # Assuming partner_id is the agent
            ('create_date', '>=', last_year_date),
            ('move_id.state', '=', 'posted')
        ])

        # Calculate the total amount paid in the past year
        if payments:
            return sum(payment.price_total for payment in payments)
        else:
            return 0.00  # Return 0.00 if no payments exist


    def calculate_deals_closing_this_week(self):
        """
        Calculate the number of deals closing this week.
        """
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Search for deals closing this week
        deals = self.search([
            ('expected_close', '>=', start_of_week),
            ('expected_close', '<=', end_of_week),
            ('partner_id', '=', self.partner_id.id)  # Assuming partner_id is the agent
        ])

        return len(deals)

    def calculate_expiring_this_month(self):
        """
        Calculate the total amount expiring this month.
        """
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Search for deals expiring this month
        deals = self.search([
            ('expected_close', '>=', start_of_month),
            ('expected_close', '<=', end_of_month),
            ('partner_id', '=', self.partner_id.id)  # Assuming partner_id is the agent
        ])

        # Calculate the total amount expiring this month
        return sum(deal.planned_revenue for deal in deals)

    def calculate_deals_closing_this_month(self):
        """
        Calculate the number of deals closing this month.
        """
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Search for deals closing this month
        deals = self.search([
            ('expected_close', '>=', start_of_month),
            ('expected_close', '<=', end_of_month),
            ('partner_id', '=', self.partner_id.id)  # Assuming partner_id is the agent
        ])

        return len(deals)