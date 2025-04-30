from datetime import datetime, timedelta
from odoo import models, fields, api
from collections import defaultdict
from calendar import monthrange


class CRMDashboard(models.Model):
    _inherit = 'crm.lead'
    _description = 'CRM Dashboard Details'

    def get_dashboard_data(self):
        """
        Compute and return dynamic data for the CRM dashboard.

        Returns:
            dict: A dictionary containing:
                - currentPayout: Current payout percentage as a string (e.g., "10%")
                - ltmCommissions: Total commissions earned in last twelve months
                - closingThisWeek: Number of deals closing this week (hardcoded for demo)
                - expiringThisMonth: Amount expiring this month (hardcoded for demo)
                - closingThisMonth: Number of deals closing this month (hardcoded for demo)
        """
        # Calculate current payout percentage
        current_payout = self.calculate_current_payout_percentage()
        # Calculate Last Twelve Months (LTM) Commissions
        ltm_commissions = self.calculate_ltm_commissions()

        # Get all won leads
        won_leads = self.env['crm.lead'].search([
            ('stage_id.is_won', '=', True)
        ])
        # Calculate total asking price (sum of commission_to_be_paid)
        totalAskingPrice = sum(
            lead.commission_to_be_paid
            for lead in won_leads
            if lead.commission_to_be_paid
        )
        # Calculate total properties (count of unique property addresses)
        property_addresses = {
            lead.x_studio_property_address
            for lead in won_leads
            if lead.x_studio_property_address
        }
        totalProperties = len(property_addresses)
        domain = [
            ('user_id', '=', self.env.user.id)
        ]
        return {
            'currentPayout': f"{current_payout}%",
            'ltmCommissions': ltm_commissions,
            'closingThisWeek': self.calculate_deals_closing_this_week(),
            'expiringThisMonth': self.calculate_expiring_this_month(),
            'closingThisMonth': self.calculate_deals_closing_this_month(),
            'totalAskingPrice': totalAskingPrice,
            'totalProperties': totalProperties,
            'avgDaysToClose': self.calculate_avg_days_to_close(),
            'avgClosePrice': self.calculate_avg_close_price(won_leads),
            'salesVolume': self.calculate_sales_volume(won_leads),
            'closedTransactions': len(won_leads),
            'leadToClientCount': self.calculate_lead_to_client_count(),
            'priceChangePercentage': self.calculate_price_change_percentage(
                won_leads),

        }

    def calculate_avg_days_to_close(self):
        """
        Calculate average days between creation date and being Won
        Returns 0 if no won leads found
        """
        won_leads = self.env['crm.lead'].search([
            ('stage_id.is_won', '=', True),
            ('create_date', '!=', False),
            ('date_last_stage_update', '!=', False)
        ])

        if not won_leads:
            return 0

        total_days = 0
        valid_leads = 0

        for lead in won_leads:
            delta = lead.date_last_stage_update.date() - lead.create_date.date()
            total_days += delta.days
            valid_leads += 1
        print(total_days,"total_days")
        return round(total_days / valid_leads) if valid_leads > 0 else 0

    def calculate_avg_close_price(self, won_leads):
        """
        Calculate average close price from won leads
        """
        if not won_leads:
            return 0

        prices = [lead.total_sales_price for lead in won_leads if
                  lead.total_sales_price]
        return sum(prices) / len(prices) if prices else 0

    def calculate_sales_volume(self, won_leads):
        """
        Calculate total sales volume from won leads
        """
        return sum(
            lead.total_sales_price for lead in won_leads if
            lead.total_sales_price)

    def calculate_lead_to_client_count(self):
        """
        Count leads that moved from New to Qualified status
        """
        qualified_leads = self.env['crm.lead'].search([
            ('stage_id.name', '=', "Qualified"), ('user_id', '=',
                                                  self.env.user.id)
        ])
        if not qualified_leads:
            return 0

        return len(qualified_leads)

    def calculate_price_change_percentage(self, won_leads):
        """
        Calculate % change from list price to sales price
        """
        if not won_leads:
            return 0

        total_percentage = 0
        valid_count = 0

        for lead in won_leads:
            if lead.total_list_price and lead.total_sales_price:
                percentage = ((
                                      lead.total_sales_price - lead.total_list_price) /
                              lead.total_list_price) * 100
                total_percentage += percentage
                valid_count += 1

        return round(total_percentage / valid_count,
                     1) if valid_count > 0 else 0

    def calculate_current_payout_percentage(self):
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
        return commission_rate * 100  # Convert to percentage

    def calculate_ltm_commissions(self):
        """
        Calculate the total commissions earned in the last twelve months.

        Returns:
            float: Total commission amount for the last 12 months
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
            ('move_id.partner_id', '=',
             self.env.user.secondary_related_partner_id.id
             if self.env.user.secondary_related_partner_id else
             self.env.user.partner_id.id),
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
        Calculate the number of deals with date_deadline falling in current week.

        Returns:
            int: Count of deals with date_deadline within current week
        """
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        # Search for deals closing this week (using date_deadline)
        deals = self.env['crm.lead'].search([
            ('date_deadline', '>=', start_of_week),
            ('date_deadline', '<=', end_of_week),
            ('user_id', '=', self.env.user.id)
            # Current user's partner
        ])
        return len(deals)

    def calculate_expiring_this_month(self):
        """
        Calculate the total amount of deals expiring this month based on date_deadline.

        Returns:
            float: Sum of planned_revenue for deals expiring this month
        """
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(
            day=1) - timedelta(days=1)

        # Search for deals expiring this month (using date_deadline)
        deals = self.search([
            ('date_deadline', '>=', start_of_month),
            ('date_deadline', '<=', end_of_month),
            ('user_id', '=', self.env.user.id)
            # Current user's partner
        ])

        return len(deals)

    def calculate_deals_closing_this_month(self):
        """
        Calculate the number of deals with date_deadline falling in current month.

        Returns:
            int: Count of deals with date_deadline within current month
        """
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(
            day=1) - timedelta(days=1)

        # Search for deals closing this month (using date_deadline)
        deals = self.search([
            ('date_deadline', '>=', start_of_month),
            ('date_deadline', '<=', end_of_month),
            ('user_id', '=', self.env.user.id)
            # Current user's partner
        ])

        return len(deals)

    @api.model
    def get_active_salespersons_count(self, years):
        """
        Returns count of active sales team members grouped by month-year.
        Only includes data up to current month (April 2025).

        Args:
            years (list): List of years to include in the analysis

        Returns:
            dict: Contains:
                - monthly_counts: Dictionary of {month-year: active_count}
                - salespersons: List of salespersons with their yearly activity totals
        """
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Query to get all active members and their active periods
        member_query = """
            SELECT 
                user_id,
                to_char(create_date, 'YYYY-MM-DD') as create_date,
                CASE WHEN active THEN '9999-12-31'
                     ELSE to_char(write_date, 'YYYY-MM-DD')
                END as end_date
            FROM 
                crm_team_member
            WHERE 
                user_id IS NOT NULL
        """
        self.env.cr.execute(member_query)
        members = self.env.cr.dictfetchall()

        # Initialize monthly counts
        monthly_counts = {}
        salespersons = {}

        # Prepare months only up to current month
        if years:
            for year in years:
                # Skip years after current year
                if year > current_year:
                    continue

                for month in range(1, 13):
                    # Skip months after current month for current year
                    if year == current_year and month > current_month:
                        continue

                    month_str = f"{year}-{month:02d}"
                    monthly_counts[month_str] = 0

        # Track active users per month
        active_users_per_month = {month: set() for month in
                                  monthly_counts.keys()}

        # Process each member's active period
        if members:
            for member in members:
                user_id = member['user_id']
                create_date = member['create_date']
                end_date = member['end_date']

                # Add to salespersons list
                if user_id not in salespersons:
                    yearly_totals = {}
                    if years is not None:
                        yearly_totals = {year: 0 for year in years if
                                         year <= current_year}

                    salespersons[user_id] = {
                        'id': user_id,
                        'name': "",  # Will be filled later
                        'yearly_totals': yearly_totals
                    }

                # Check which months this member was active
                for month in monthly_counts.keys():
                    year_month = month.split('-')
                    year = int(year_month[0])
                    month_num = int(year_month[1])

                    # Create date objects for comparison
                    month_start = f"{year}-{month_num:02d}-01"
                    last_day = monthrange(year, month_num)[1]
                    month_end = f"{year}-{month_num:02d}-{last_day}"

                    if (create_date <= month_end) and (
                            end_date >= month_start):
                        active_users_per_month[month].add(user_id)

        # Get salesperson names
        user_ids = list(salespersons.keys())
        if user_ids:
            users = self.env['res.users'].browse(user_ids)
            for user in users:
                if user.id in salespersons:
                    salespersons[user.id]['name'] = user.name

        # Convert sets to counts
        for month, users in active_users_per_month.items():
            monthly_counts[month] = len(users)

            # Update yearly totals for salespersons
            year = int(month.split('-')[0])
            for user_id in users:
                if year in salespersons[user_id]['yearly_totals']:
                    salespersons[user_id]['yearly_totals'][year] += 1

        return {
            'monthly_counts': monthly_counts,
            'salespersons': list(salespersons.values())
        }

    @api.model
    def get_dashboard_year_data(self, years):
        """
        Get combined dashboard data including lead and commission information.

        Args:
            years (list): List of years to include in the analysis

        Returns:
            dict: Contains:
                - lead_data: Salesperson activity data
                - commission_data: Commission and transaction data
        """
        # Get lead data
        lead_data = self.get_active_salespersons_count(years)

        # Get commission data
        commission_data = self.get_commission_data(years)

        return {
            'lead_data': lead_data,
            'commission_data': commission_data
        }

    @api.model
    def get_commission_data(self, years):
        """
        Calculate commission data grouped by year and month.

        Args:
            years (list): List of years to include in the analysis

        Returns:
            dict: Contains:
                - commissions: Dictionary of {year: monthly_commission_totals}
                - transactions: Dictionary of {year: monthly_transaction_counts}
        """
        if not years:
            return {}

        commissions = {year: [0] * 12 for year in years}
        transactions = {year: [0] * 12 for year in years}

        won_leads = self.env['crm.lead'].search([
            ('create_date', '>=', f"{min(years)}-01-01"),
            ('create_date', '<=', f"{max(years)}-12-31"),
            ('stage_id.is_won', '=', True)
        ])

        for lead in won_leads:
            year = lead.create_date.year
            month = lead.create_date.month

            if year in commissions:
                # Determine commission amount based on company name
                if lead.company_id and 'Residential' in (
                        lead.company_id.name or ''):
                    commission_amount = lead.commission_to_be_paid or 0
                else:
                    commission_amount = lead.total_commercial_commission_earned or 0

                # Update commission and transaction counts
                commissions[year][month - 1] += commission_amount
                transactions[year][month - 1] += 1

        return {
            'commissions': commissions,
            'transactions': transactions
        }
