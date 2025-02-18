# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.tools import date_utils


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """Overwriting the 'create_invoices' function to add the next bill date calculation"""
        sale_order = self.sale_order_ids
        self._check_amount_is_positive()
        invoices = self._create_invoices(self.sale_order_ids)
        # Updating the Next bill date
        if invoices and sale_order.is_rental_order:
            for lines in invoices.line_ids.sale_line_ids:
                if not lines.product_template_id.charges_ok:
                    start_date = lines.next_bill_date

                    billing_period_unit = sale_order.recurring_plan_id.billing_period_unit
                    billing_period_value = sale_order.recurring_plan_id.billing_period_value

                    if billing_period_unit == "day":
                        lines.next_bill_date = date_utils.add(start_date, days=billing_period_value)
                    elif billing_period_unit == "month":
                        lines.next_bill_date = date_utils.add(start_date, months=billing_period_value)
                    elif billing_period_unit == "year":
                        lines.next_bill_date = date_utils.add(start_date, years=billing_period_value)
                    else:
                        raise ValueError(f"Unsupported billing_period_unit: {billing_period_unit}")
        return self.sale_order_ids.action_view_invoice(invoices=invoices)