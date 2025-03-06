# -*- coding: utf-8 -*-

import datetime

# from addons.product.models.product_template import PRICE_CONTEXT_KEYS
from odoo import models, fields, _
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import pytz
from odoo.tools import date_utils


class ImportFileWizard(models.TransientModel):
    _name = "import.file.wizard"
    _description = "Import File Wizard"

    file = fields.Binary(string="File To Import", required=True)

    def normalize_datetime(self, date_value):
        """ Convert date format to '%Y-%m-%d %H:%M:%S' if necessary. Return as is if already in correct format. """
        if not date_value:
            return None  # Skip if no date is provided
        # If the value is already a datetime object, format it correctly
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d %H:%M:%S")
        date_str = str(date_value) # Convert to string if not already
        date_formats = [
            "%Y-%m-%d %H:%M:%S",  # Correct format
            "%Y-%m-%d",  # YYYY-MM-DD (without time)
            "%d-%m-%Y %H:%M:%S",  # DD-MM-YYYY HH:MM:SS
            "%d-%m-%Y",  # DD-MM-YYYY (without time)
            "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY HH:MM:SS
            "%d/%m/%Y",  # DD/MM/YYYY (without time)
        ]  # Define acceptable formats
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # If time is missing, default to '00:00:00'
                return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        raise ValidationError(
            f"Invalid date format: {date_str}. Expected formats: YYYY-MM-DD HH:MM:SS, DD-MM-YYYY, DD/MM/YYYY, etc.")

    def action_import_rental_order(self):
        """ Create rental orders and order lines through the 'Import' button action """
        try:
            wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)), read_only=True)
            ws = wb.active
            order_obj = self.env["sale.order"]
            partner_obj = self.env["res.partner"]
            product_obj = self.env["product.template"]
        # Mapping imported values to match the selection field
            bill_terms_mapping = {'Advance Bill': 'advance','Not Advance Bill': 'late'}
            created_orders = []
        # Dictionary to store serial number → delivery date mapping
            serial_delivery_date_map = {}
            serial_delivery_date_order_map = {}
            serial_pickup_date_map = {}
            serial_pickup_date_order_map = {}
            serial_delivery_driver_map = {}
            serial_pickup_driver_map = {}
            counter = 0
            for row in ws.iter_rows(min_row=2):
                # counter += 1
                # if counter > 13:
                #     break
                order_ref = row[0].value
                order_date = row[1].value
                customer_name = row[2].value.strip() if row[2].value else None
                company_name = row[5].value.strip() if row[5].value else None
                company_id = self.env['res.company'].search([('name', '=', company_name)], limit=1)
                warehouse_name = row[6].value.strip() if row[6].value else None
                rental_start_date = self.normalize_datetime(row[15].value)  # Converting to odoo's date format
                rental_end_date = self.normalize_datetime(row[16].value)  # Converting to odoo's date format
                next_bill_date = self.normalize_datetime(row[26].value)
                product_name = row[17].value.strip() if row[17].value else None
                product_qty = row[20].value
                unit_price = row[27].value
                recurring_plan = row[8].value
                price_list = row[4].value.strip() if row[4].value else None
                bill_terms = row[9].value.strip() if row[9].value else None
                bill_terms = bill_terms_mapping.get(bill_terms, 'late')  # Default to 'late' if invalid
                is_sale = 1 if "TRUE" in str(row[32].value).strip().upper() else 0
                is_rental = 1 if "TRUE" in str(row[33].value).strip().upper() else 0
                is_service_charge = 1 if "TRUE" in str(row[34].value).strip().upper() else 0
                picked_lot = row[45].value if row[45].value else None
                importing_external_id = row[44].value if row[44].value else None
                picked_lot_ids = self.env["stock.lot"]
                delivery_driver = row[41].value if row[41].value else None
                pickup_driver = row[43].value if row[43].value else None
            # Get Drivers
                if delivery_driver:
                    delivery_driver_id = partner_obj.search([('name', '=', delivery_driver.strip())], limit=1)
                    if not delivery_driver_id:
                        raise ValidationError (f"Delivery Driver '{delivery_driver}' is not found. Please create it first. ")
                if pickup_driver:
                    pickup_driver_id = partner_obj.search([('name', '=', pickup_driver.strip())], limit=1)
                    if not pickup_driver_id:
                        raise ValidationError (f"Pick-Up Driver '{pickup_driver}' is not found. Please create it first. ")
            # Store serial number and values in dictionaries
                serial_number = row[38].value if row[38].value else None
                delivery_date = self.normalize_datetime(row[40].value) if row[40].value else None
                pickup_date = row[42].value if row[42].value else None
                if serial_number and delivery_date:
                    serial_delivery_date_map[serial_number] = delivery_date
                    serial_delivery_date_order_map[delivery_date] = order_ref
                if serial_number and pickup_date:
                    serial_pickup_date_map[serial_number] = pickup_date
                    serial_pickup_date_order_map[pickup_date] = order_ref
                if serial_number and delivery_driver:
                    serial_delivery_driver_map[serial_number] = delivery_driver
                if serial_number and pickup_driver:
                    serial_pickup_driver_map[serial_number] = pickup_driver
                if serial_number and not picked_lot :
                        picked_lot = serial_number
                if not ([order_ref and order_date and customer_name and product_name and price_list]):
                    continue
                if (order_ref and order_date and customer_name and price_list and  row[18].value):
            # Get Customer
                    customer = partner_obj.search([('name', '=', customer_name)], limit=1)
                    if not customer:
                        raise UserError(f"Customer '{customer_name}' in the order {order_ref},is not found. Please create it first.")
            # Get Product
                    if product_name:
                        product = product_obj.search([('name', 'ilike', product_name)], limit=1)
                        print('product name',product.name,order_ref)
                        if not product:
                            raise UserError(f"Product '{product_name}'  in the order {order_ref},is not found. Please create it first.")
            # Get or Create serial numbers
                    if picked_lot:
                        if not product.charges_ok:
                            lot_names = [lot.strip() for lot in picked_lot.split(",")]  # Split and strip spaces
                            picked_lot_ids = self.env["stock.lot"].search([('name', 'in', lot_names)])
                            if not picked_lot_ids or len(picked_lot_ids) < len(lot_names):
                                existing_lot_names = picked_lot_ids.mapped('name')  # Get already existing lot names
                                new_lots = []
                                for name in lot_names:
                                    if name not in existing_lot_names:  # Avoid duplication
                                        new_lot = self.env["stock.lot"].create(
                                            {'name': name, 'product_id': product.id, 'product_qty': 1,'company_id': company_id.id})
                                        stock_location = self.env['stock.location'].search([('company_id','=',company_id.id),
                                                                                         ('usage','=','internal'),
                                                                                         ('replenish_location','=',True),])
                                        self.env["stock.quant"].create([{'location_id': stock_location.id,
                                                                         'product_id': product.id,
                                                                         'lot_id': new_lot.id,
                                                                         'in_date': order_date,
                                                                         'inventory_quantity': 1.0}]).action_apply_inventory()
                                        stock_valuation_layer = self.env['stock.valuation.layer'].search([('company_id','=',company_id.id),
                                                                                  ('product_id', '=', product.id),
                                                                                  ('lot_id','=', new_lot.id)])
                                        if stock_valuation_layer:
                                            query = """
                                                UPDATE stock_valuation_layer
                                                SET create_date = %s
                                                WHERE id = %s
                                            """
                                            params = (order_date, stock_valuation_layer.id)
                                            self.env.cr.execute(query, params)
                                            stock_valuation_layer.stock_move_id.write({'date': order_date})
                                            stock_valuation_layer.stock_move_id.move_line_ids.write({'date': order_date})
                                        new_lots.append(new_lot.id)
                                # Merge newly created lots with already existing ones
                                picked_lot_ids |= self.env["stock.lot"].browse(new_lots)
                    else:
                        picked_lot_ids = None
            # Check if Order Already Exists
                    rental_order = order_obj.search([('name', '=', order_ref)], limit=1)
            # creating new order
                    if not rental_order:
                        price_list_name = price_list.split(" (")[0]  # Extracts "ICT" from "ICT (USD)"
                        rental_order = order_obj.create([{
                            'name': order_ref,
                            'date_order': order_date,
                            'partner_id': customer.id,
                            'pricelist_id': self.env['product.pricelist'].search([('name', '=', price_list_name)], limit=1).id,
                            'company_id': self.env['res.company'].search([('name', '=', company_name)], limit=1).id,
                            'warehouse_id': self.env['stock.warehouse'].search([('name', '=', warehouse_name)], limit=1).id,
                            'recurring_plan_id': self.env['rental.recurring.plan'].search([('name', '=', recurring_plan)],
                                                                                          limit=1).id,
                            'is_rental_order': True,
                            'bill_terms': bill_terms,
                            'rental_start_date': rental_start_date,
                            'rental_return_date': rental_end_date,
                            'order_line': []
                        }])
                        created_orders.append(rental_order)
            # Add Order Line
                    if row[19].value and row[19].value.strip() == 'Section':
                        order_line_vals = {
                            'order_id': rental_order.id,
                            'name': row[18].value,
                            'display_type': 'line_section',
                            'sequence': row[35].value,
                            'importing_external_id': importing_external_id if importing_external_id else None,
                        }
                    elif not row[19].value:
                        order_line_vals = {
                            'order_id': rental_order.id,
                            'product_id': product.id,
                            'display_type': False,
                            'sequence': row[35].value,
                            'is_sale': is_sale,
                            'is_rental': is_rental,
                            'is_service_charge': is_service_charge,
                            'product_uom_qty': product_qty or 1,
                            'price_unit': float(unit_price),
                            'rental_start_date': rental_start_date,
                            'rental_end_date': rental_end_date,
                            'next_bill_date': next_bill_date,
                            'rental_pickable_lot_ids': picked_lot_ids if picked_lot_ids else None,
                            # 'returned_lot_ids': returned_lot_ids if returned_lot_ids else None,
                            'importing_external_id': importing_external_id if importing_external_id else None,
                        }
                    order_line = self.env['sale.order.line'].with_context(import_from_sheet=True).create(order_line_vals)
            for order in created_orders:
                order.with_context(import_from_sheet=True)._prepare_confirmation_values()
                order.with_context(import_from_sheet=True).action_confirm()
                action_dict = order.action_open_pickup()
                pickup_wizard = self.env['rental.order.wizard'].with_context(action_dict['context']).create({})
                pickup_wizard._get_wizard_lines()
                pickup_wizard.apply()
                for line in order.order_line:
                    if line.rental_pickable_lot_ids:
                        for lot in line.rental_pickable_lot_ids:
                            if lot.name in serial_pickup_date_map and order.name in serial_pickup_date_order_map.values():
                                return_action_dict = order.action_open_return()
                                return_wizard = self.env['rental.order.wizard'].with_context(return_action_dict['context']).create({})
                                return_wizard._get_wizard_lines()
                                for line in return_wizard.rental_wizard_line_ids:
                                    if line.product_id == lot.product_id:
                                        line.returned_lot_ids = lot
                                    else:
                                        line.qty_returned = 0
                                return_wizard.apply()
                # Update the delivery date of Stock move and Stock move line
                for line in order.order_line.filtered(lambda l: l.rental_pickable_lot_ids):
                    for lot in line.rental_pickable_lot_ids:
                        # delivery_date = serial_delivery_date_map.get(lot.name)
                        delivery_date = next((key for key, value in serial_delivery_date_order_map.items() if value == order.name), None)
                        return_date = serial_pickup_date_map.get(lot.name)
                        delivery_driver = serial_delivery_driver_map.get(lot.name)
                        pickup_driver = serial_pickup_driver_map.get(lot.name)
                        return_date_record = self.env['product.return.dates'].search([
                            ('serial_number', '=', lot.id),
                            ('order_id', '=', order.id),
                            ('order_line_id', '=', line.id)
                        ], limit=1)
                        if return_date_record:
                                # To change the date of Stock move and Stock move line creation.
                                moves_to_update = order.mapped('order_line.move_ids.move_line_ids').filtered(
                                    lambda m: m.lot_id.id == lot.id)
                                if moves_to_update:
                                    for move_line in moves_to_update:
                                        if return_date and serial_pickup_date_order_map[return_date] == order.name:
                                            return_date_record.write({'return_date': return_date})
                                            if any(loc.name == 'Rental' for loc in move_line.location_id):
                                                move_line.write({'date': return_date})
                                                move_line.move_id.write({'date': return_date})
                                        if delivery_date  and serial_delivery_date_order_map[delivery_date] == order.name :
                                            return_date_record.write({'delivery_date': delivery_date})
                                            if any(loc.name == 'Stock' for loc in move_line.location_id):
                                                move_line.write({'date': delivery_date})
                                                move_line.move_id.write({'date': delivery_date})
                            # To add the delivery driver and pick up driver
                                if delivery_driver:
                                    delivery_driver_id = partner_obj.search([('name', '=', delivery_driver.strip())], limit=1)
                                    if delivery_driver_id:
                                        return_date_record.write({'delivery_driver': delivery_driver_id})
                                if  pickup_driver:
                                    pickup_driver_id = partner_obj.search([('name', '=', pickup_driver.strip())], limit=1)
                                    if pickup_driver_id:
                                        return_date_record.write({'pickup_driver': pickup_driver_id})
            # raise ValidationError('Success')
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': f"{len(created_orders)} Rental Orders Imported Successfully! \n",
                    'type': 'rainbow_man',
                },
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except ValidationError as e:
            raise e