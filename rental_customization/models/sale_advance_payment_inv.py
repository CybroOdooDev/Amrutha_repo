# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.tools import date_utils


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """Overwriting the 'create_invoices' function to add the next bill date calculation"""
        sale_order = self.sale_order_ids
        if sale_order.is_rental_order:
            self._check_amount_is_positive()
            sale_order.with_context(button_action=True).generate_recurring_bills()
            return self.sale_order_ids.action_view_invoice()