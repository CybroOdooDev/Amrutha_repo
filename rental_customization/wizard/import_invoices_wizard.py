# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields, _
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
import pytz
from odoo.tools import date_utils


class ImportInvoicesWizard(models.TransientModel):
    _name = "import.invoices.wizard"
    _description = "Import Invoices Wizard"

    file = fields.Binary(string="File To Import",required=1)

    def action_import_invoices(self):
        """ Create rental orders and order lines through the 'Import' button action """
        wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)), read_only=True)
        ws = wb.active

        invoice_obj = self.env["account.move"]
        partner_obj = self.env["res.partner"]
        product_obj = self.env["product.product"]
        created_invoices = []  # Track created invoices
        for row in ws.iter_rows(min_row=2):
            invoice_ref = row[0].value
            status_in_payment = row[1].value
            customer_name = row[3].value.strip() if row[2].value else None
            invoice_origin = row[5].value.strip() if row[2].value else None
            invoice_date = row[6].value
            invoice_date_due = row[7].value
            journal_name = row[8].value.strip() if row[2].value else None
            company_name = row[9].value.strip() if row[2].value else None
            company_id = self.env['res.company'].search([('name', '=', company_name)], limit=1).id
            payment_ref = row[10].value.strip() if row[10].value else None
            product_name = row[14].value.strip() if row[14].value else None
            line_label = row[15].value.strip() if row[15].value else None
            product_qty = row[17].value
            unit_price = row[18].value
            sale_line_external_id =  row[21].value.strip() if row[21].value else None
            if sale_line_external_id:
                sale_order_line_id = self.env["sale.order.line"].search([('importing_external_id', '=', sale_line_external_id)], limit=1)
        # Skip empty rows
            if not ([invoice_ref and invoice_date and customer_name and product_name]):
                continue
            if (invoice_ref and invoice_date and customer_name and product_name):
        # Get or create Customer
                customer = partner_obj.search([('name', '=', customer_name)], limit=1)
                if not customer:
                    raise UserError(f"Customer '{customer_name}' in the invoice {invoice_ref},is not found. Please create it first.")
        # Get or create Product
                product = product_obj.search([('name', '=', product_name)], limit=1)
                if not product:
                    raise UserError(f"Product '{product_name}' in the invoice {invoice_ref},is not found. Please create it first.")
        # Check if Order Already Exists
                invoice = invoice_obj.search([('name', '=', invoice_ref)], limit=1)
        # creating new order
                if not invoice:
                    invoice = invoice_obj.create([{
                        'name': invoice_ref,
                        'invoice_date': invoice_date,
                        'invoice_date_due': invoice_date_due,
                        'journal_id': self.env['account.journal'].search([('name', '=', journal_name)], limit=1).id,
                        'partner_id': customer.id,
                        'invoice_origin': invoice_origin,
                        'company_id': company_id,
                        'payment_reference': payment_ref ,
                        'move_type':'out_invoice',
                        'invoice_line_ids': []
                    }])
                    created_invoices.append(invoice)
        # Add Order Line
                if product:
                    invoice_line_vals = {
                        'move_id': invoice.id,
                        'product_id': product.id,
                        'name': line_label,
                        'quantity': product_qty,
                        'price_unit': unit_price,
                    # connecting the invoice line to the corresponding sale order line
                        'sale_line_ids':sale_order_line_id if sale_order_line_id else None,
                    }
                invoice_line = self.env['account.move.line'].create(invoice_line_vals)
    # connecting the sale order line to the corresponding invoice line
        if sale_order_line_id:
                    sale_order_line_id.invoice_lines = invoice_line
        for invoice in created_invoices:
            invoice.action_post()
            invoice.write({'payment_state':'paid'})
        # raise ValidationError('success')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': f"{len(created_invoices)} Invoices Imported Successfully! \n",
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.client',
            'tag': 'reload',
        }