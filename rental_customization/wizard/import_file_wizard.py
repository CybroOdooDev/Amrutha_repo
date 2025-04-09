# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, _
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import pytz
from odoo.tools import date_utils
import logging
_logger = logging.getLogger(__name__)


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
            product_obj = self.env["product.product"]
            bill_terms_mapping = {'Advance Bill': 'advance','Not Advance Bill': 'late'}
            created_orders = []
            serial_delivery_date_map = {}
            serial_delivery_date_order_map = {}
            serial_pickup_date_map = {}
            serial_pickup_date_order_map = {}
            serial_delivery_driver_map = {}
            serial_pickup_driver_map = {}
            line_qty_delivered = {}

            no_product = []
            no_customer = []
            no_serial = []
            not_in_company =[]
            serial_from_another_company =[]
            skipped_orders = []
            used_serials = []
            ignored_already_used_serail = []
            skip_line = False
            counter = 0
            for row in ws.iter_rows(min_row=2):
                skip_line = False
                # counter += 1
                # if counter > 21:
                #     break
                order_ref = row[0].value
                order_date = row[1].value
                customer_name = row[2].value.strip() if row[2].value else None
                delivery_address = row[3].value.strip() if row[3].value else None
                company_name = row[5].value.strip() if row[5].value else None
                company_id = self.env['res.company'].search([('name', '=', company_name)], limit=1)
                warehouse_name = row[6].value.strip() if row[6].value else None
                rental_start_date = self.normalize_datetime(row[15].value)  # Converting to odoo's date format
                rental_end_date = self.normalize_datetime(row[16].value)  # Converting to odoo's date format
                next_bill_date = self.normalize_datetime(row[26].value)
                product_name = row[17].value.strip() if row[17].value and isinstance(row[17].value, str) else None
                description = row[18].value.strip() if row[18].value and isinstance(row[18].value, str) else None
                product_qty = row[20].value
                qty_delivered = row[21].value
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
                serial_number = row[38].value if row[38].value else None
                delivery_date = self.normalize_datetime(row[40].value) if row[40].value else None
                pickup_date = row[42].value if row[42].value else None
                if not (order_ref and order_date and customer_name):
                    break
                if not description:
                    skipped_orders.append(order_ref)
                    continue
                if not product_name and not row[19].value:
                    skipped_orders.append(order_ref)
                    continue
            # Get Drivers - (pasted to the last)
            # Store serial number and values in dictionaries
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
                if importing_external_id and qty_delivered:
                    line_qty_delivered[importing_external_id]=qty_delivered
                if not ([order_ref and order_date and customer_name and product_name and price_list]):
                    continue
                if (order_ref and order_date and customer_name and  row[18].value):
            # Get Customer
                    customer = partner_obj.search([('name', '=', customer_name)], limit=1)
                    if not customer:
                        customer = partner_obj.search(['|',('name', '=', customer_name.upper()),('name', '=', customer_name.lower())], limit=1)
                        if not customer:
                            no_customer.append(customer_name)
                            customer = partner_obj.create([{'name': customer_name,
                                                             'company_id': company_id.id,}])
                        # raise UserError(f"Customer '{customer_name}' in the order {order_ref},is not found. Please create it first.")
                    shipping_addr = partner_obj.search([('name', '=', delivery_address)], limit=1)
            # Get Product
                    if product_name:
                        product = product_obj.search(['|',('name', '=', product_name),('default_code', '=', product_name)], limit=1)
                        if not product:
                            product_name_cleaned = product_name.replace(" ", "")
                            product = product_obj.search([
                                ('rent_ok', '=', True),'|',
                                ('name', '=', product_name_cleaned),
                                ('default_code', '=', product_name_cleaned)
                            ], limit=1)
                            if not product:
                                product = product_obj.search([('name', '=', description)], limit=1)
                                if not product:
                                    product = product_obj.search([('description_sale', '=', description)], limit=1)
                                    if not product:
                                        no_product.append(product_name)
                                        # cleaned_text = description.replace(product_name, "",1)  # The `1` ensures only the first occurrence is removed
                                        skipped_orders.append(order_ref)
                                        continue
                                        # raise UserError(f"Product '{product_name}' in the order {order_ref},is not found. Please create it first.")
                        if product and product.company_id and (product.company_id != company_id and product.company_id != company_id.parent_id):
                            not_in_company.append(product_name)
                            skipped_orders.append(order_ref)
                            continue
                            # raise UserError(f"Product '{product_name}' in the order {order_ref},belongs to another company ")
            # Get Pricelist
                    if price_list:
                        price_list_name = price_list.split(" (")[0]  # Extracts "ICT" from "ICT (USD)"
                        pricelist = self.env['product.pricelist'].search([('name', '=', price_list_name),('company_ids','=',company_id.id)], limit=1)
                        if not pricelist:
                            pricelist = self.env['product.pricelist'].search(
                                [('name', '=', 'Default'), ('company_id', '=', company_id.id)], limit=1)
                            if not pricelist:
                                raise UserError(f"Pricelist '{price_list_name}' in the order {order_ref},is not found. Please create it first.")
                    else:
                        pricelist = self.env['product.pricelist'].search([('name', '=', 'Default'),('company_id','=',company_id.id)], limit=1)
            # Get  serial numbers
                    if picked_lot:
                        if not product.charges_ok:
                            picked_lot_str = str(picked_lot)
                            lot_names = [lot.strip().replace(" ", "") for lot in picked_lot_str.split(",")] if "," in picked_lot_str else [picked_lot_str]
                            if lot_names:
                                for lot in lot_names:
                                    if lot  in used_serials:
                                        lot_names.remove(lot)
                                        ignored_already_used_serail.append(lot)
                                    else:
                                        used_serials.append(lot)
                                    if lot not in ['NULL','Null','null']:
                                        lot = lot.upper().strip()
                                        picked_lots = self.env["stock.lot"].search([('name', '=', lot)])
                                        # if picked_lots and picked_lots.company_id and picked_lots.company_id != company_id and picked_lots.company_id != company_id.parent_id:
                                        #     serial_from_another_company.append(lot)
                                        #     skipped_orders.append(order_ref)
                                        #     # raise ValidationError (f'serial not in company or parent company, {lot}')
                                        #     continue
                                        # if picked_lots and picked_lots.company_id and picked_lots.company_id != company_id and picked_lots.company_id == company_id.parent_id:
                                        if picked_lots and picked_lots.company_id and picked_lots.company_id != company_id:
                                            serial_from_another_company.append(lot)
                                            skipped_orders.append(order_ref)
                                            skip_line = True
                                            continue
                                        if not picked_lots:
                                            no_serial.append(lot)
                                            stock_loc = self.env['stock.location'].search(
                                                [('company_id', '=', company_id.id), ('name', '=', 'Stock')])
                                            picked_lots = self.env["stock.lot"].create([{'name': lot,
                                                                                     'product_id': product.id,
                                                                                     'company_id': company_id.id if company_id else None,
                                                                                     'location_id': stock_loc.id if stock_loc else None}])
                                            self.env["stock.quant"].create([{'location_id': stock_loc.id if stock_loc else None,
                                                                             'product_id': product.id,
                                                                             'lot_id': picked_lots.id,
                                                                             'inventory_quantity': 1.0}]).action_apply_inventory()
                                            # raise ValidationError(f'Lot/Serial Number {lot} in the order {order_ref},is not found. Please create it first.')
                                if skip_line :
                                    continue
                                picked_lot_ids = self.env["stock.lot"].search([('name', 'in', lot_names)])
                                # picked_lot_ids = self.env["stock.lot"].search([('name', 'in', lot_names)])
                    else:
                        picked_lot_ids = None
            # Check if Order Already Exists
                    rental_order = order_obj.search([('name', '=', order_ref)], limit=1)
            # creating new order
                    if not rental_order:
                        rental_order = order_obj.create([{
                            'name': order_ref,
                            'date_order': order_date,
                            'partner_id': customer.id,
                            'partner_shipping_id': shipping_addr if shipping_addr else customer.id,
                            'pricelist_id': pricelist.id if pricelist else None,
                            'company_id': self.env['res.company'].search([('name', '=', company_name)], limit=1).id,
                            'warehouse_id': self.env['stock.warehouse'].search([('name', '=', warehouse_name)], limit=1).id,
                            'recurring_plan_id': self.env['rental.recurring.plan'].search([('name', '=', recurring_plan)],limit=1).id,
                            'is_rental_order': True,
                            'bill_terms': bill_terms,
                            'rental_start_date': rental_start_date,
                            'rental_return_date': rental_end_date,
                            'imported_order': True,
                            'order_line': [],
                        }])
                        created_orders.append(rental_order)
            # Add Order Line
            # Search for existing order line
                    existing_order_line = self.env['sale.order.line'].search([
                        ('order_id', '=', rental_order.id),
                        ('sequence', '=', row[35].value),
                        ('importing_external_id', '=', importing_external_id)
                    ], limit=1)
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
                            'name' : product_name,
                            'display_type': False,
                            'sequence': row[35].value,
                            'is_sale': is_sale,
                            'is_rental': True,
                            'is_service_charge': is_service_charge,
                            'product_uom_qty': product_qty or 1,
                            'price_unit': float(unit_price),
                            'rental_start_date': rental_start_date,
                            'rental_end_date': rental_end_date,
                            'next_bill_date': next_bill_date,
                            'rental_pickable_lot_ids': picked_lot_ids if picked_lot_ids else None,
                            # 'returned_lot_ids': returned_lot_ids if returned_lot_ids else None,
                            'importing_external_id': importing_external_id if importing_external_id else None,
                            'need_bill_importing': True if row[46].value and row[46].value.strip() == 'Bill' else False,
                        }
                    if existing_order_line:
                        existing_order_line.with_context(import_from_sheet=True).write(order_line_vals)
                    else:
                        order_line = self.env['sale.order.line'].with_context(import_from_sheet=True).create(order_line_vals)
            # raise ValidationError('stop')
            for order in created_orders:
                order.with_context(import_from_sheet=True)._prepare_confirmation_values()
                order.with_context(import_from_sheet=True).with_context(import_from_sheet=True).action_confirm()
                action_dict = order.with_context(import_from_sheet=True).action_open_pickup()
                pickup_wizard = self.env['rental.order.wizard'].with_context(action_dict['context']).create({})
                pickup_wizard._get_wizard_lines()
                lines= pickup_wizard.rental_wizard_line_ids.filtered(lambda p:p.product_id.charges_ok)
                lines.sudo().unlink()
                pickup_wizard.with_context(import_from_sheet=True).apply()
                for line in order.order_line:
            #updating all line's qty_delivered
                    if line.importing_external_id in line_qty_delivered:
                        line.qty_delivered = line_qty_delivered[line.importing_external_id]
            #Return
                    if line.rental_pickable_lot_ids:
                        for lot in line.rental_pickable_lot_ids:
                            if lot.name in serial_pickup_date_map and order.name in serial_pickup_date_order_map.values():
                                return_action_dict = order.action_open_return()
                                return_wizard = self.env['rental.order.wizard'].with_context(return_action_dict['context']).create({})
                                return_wizard._get_wizard_lines()
                                lines = return_wizard.rental_wizard_line_ids.filtered(lambda p: p.product_id.charges_ok)
                                lines.sudo().unlink()
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
            _logger.info('no_product',no_product)
            _logger.info('no_customer',no_customer)
            _logger.info('no_serial',no_serial)
            _logger.info('not_in_company',not_in_company)
            _logger.info('serial_from_another_company',serial_from_another_company)
            _logger.info('skipped_orders',skipped_orders)
            _logger.info('ignored_already_used_serail',ignored_already_used_serail)
            _logger.info('created_orders',len(created_orders))
            raise ValidationError('Success')
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

 # if delivery_driver:
    #         delivery_driver_id = partner_obj.search([('name', '=', delivery_driver.strip())], limit=1)
    #         if not delivery_driver_id:
    #             raise ValidationError (f"Delivery Driver '{delivery_driver}' is not found. Please create it first. ")
    #     if pickup_driver:
    #         pickup_driver_id = partner_obj.search([('name', '=', pickup_driver.strip())], limit=1)
    #         if not pickup_driver_id:
    #             raise ValidationError (f"Pick-Up Driver '{pickup_driver}' is not found. Please create it first. ")