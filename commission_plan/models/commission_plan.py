# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from collections import defaultdict


class CommissionPlan(models.Model):
    _name = "commission.plan"
    _description = "Tiers"

    name = fields.Char(string="Name", help="Name of the Commission Plan")
    company_ids = fields.Many2many('res.company', string="Companies")
    user_ids = fields.Many2many(comodel_name='res.users',
                                string="Salespersons", help="Salesperson "
                                                            "assigned to this commission Plan")
    start_date = fields.Date(
        'Start Date', store=True, tracking=True,
        help="Start date of the Commission Plan")
    stop_date = fields.Date(
        'End Date', store=True, tracking=True,
        help="End date of the Commission plan")
    tier_ids = fields.One2many('tier.tier', 'commission_id',
                               string='Tier of Split ')
    commission_amount_ids = fields.One2many('commission.amount',
                                            'commission_id',
                                            string="Commission Amount")

    def commission_calculation(self):

        # Step 1: Find sale orders with date_order within the date range
        sale_orders = self.env['sale.order'].search([
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.stop_date)
        ])

        # Step 2: Find leads that are linked to these sale orders and meet other criteria
        leads = self.env['crm.lead'].search([
            ('stage_id.is_won', '=', True),  # Won state
            ('_is_applicable_for_commission', '=', True),
            ('user_id', 'in', self.user_ids.ids),
            # Check if the salesperson is in self.user_ids
            ('company_id', 'in', self.company_ids.ids),
            # Check if the company is in self.company_ids
            ('order_ids', 'in', sale_orders.ids)
            # Check if lead has at least one sale order in the filtered sale orders
        ])

        from collections import defaultdict
        salesperson_leads = defaultdict(list)
        for lead in leads:
            salesperson_leads[lead.user_id].append(lead)

        # Step 4: Iterate over each salesperson and calculate total sale_amount_total
        for salesperson, lead_list in salesperson_leads.items():
            total_sale_order_count = sum(
                lead.sale_amount_total for lead in lead_list)
            # Step 5: Check tiers and calculate commission
            commission_percentage = 0
            for tier in self.tier_ids.sorted('amount',
                                             reverse=False):  # Sort tiers by amount (smallest to largest)
                if total_sale_order_count >= tier.amount:
                    commission_percentage = tier.commission_percentage  # Keep updating until we find the highest applicable tier
            # Step 6: Calculate total commission for this salesperson
            total_commission = total_sale_order_count * (
                        commission_percentage / 100)

            # Step 7: Check if the commission record for this salesperson already exists
            commission_record = self.env['commission.amount'].search([
                ('user_id', '=', salesperson.id),
                ('commission_id', '=', self.id)
            ], limit=1)  # Search for existing commission record

            if commission_record:
                # Step 8: If record exists, update the amount
                commission_record.amount = total_commission
                print(
                    f"Updated Commission for {salesperson.name}: {commission_record.amount}")
            else:
                # Step 9: If no record exists, create a new one
                self.env['commission.amount'].create({
                    'user_id': salesperson.id,
                    'commission_id': self.id,
                    'amount': total_commission,
                })
