# -*- coding: utf-8 -*-

from odoo import api,models, fields, Command


class SaleOrder(models.Model):
    """To add new fields in the sale and rental orders"""
    _inherit = "sale.order"

    customer_po = fields.Char()
    total_invoiced_amount = fields.Monetary(
        string="Total Invoiced Amount",
        compute="_compute_total_invoiced_amount",
        currency_field="currency_id",
        store=True)

    @api.depends('customer_po','invoice_count','invoice_ids.state', 'invoice_ids.amount_total')
    def _compute_total_invoiced_amount(self):
        """Compute total invoiced amount for sale orders with a customer PO"""
        for order in self:
            if order.customer_po:
                invoices = order.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'posted'))
                order.total_invoiced_amount = sum(invoices.mapped('amount_total'))
            else:
                order.total_invoiced_amount = 0.0