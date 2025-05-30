# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.tools import SQL



class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        """When an invoice is deleted, it should be reflected in the invoice count of the corresponding line in the date details with the same lot name"""
        for invoice in self:
            for line in invoice.line_ids:
                if line.sale_line_ids.order_id and not line.sale_line_ids.order_id.imported_order:
                    if line.name.startswith("Rental with Per Day Charge - "):
                        # Extract the lot name
                        lot_name = line.name.replace("Rental with Per Day Charge - ", "").strip()
                        lot = self.env['stock.lot'].search([('name', '=', lot_name)])
                        if lot:
                            for lot in lot:
                                # Find the corresponding product.return.dates record
                                date_lines = self.env['product.return.dates'].search([
                                    ('order_id', '=', line.sale_line_ids.order_id.id),
                                    ('serial_number', '=', lot.id),
                                ])
                                if date_lines and date_lines.invoice_count > 0:
                                    # Decrement the invoice count
                                    date_lines.invoice_count -= 1
        return super(AccountMove, self).unlink()

