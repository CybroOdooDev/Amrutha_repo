# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, _
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
import pytz
from odoo.tools import date_utils
import logging
logger = logging.getLogger(__name__)

class ImportLotSerialNumberWizard(models.TransientModel):
    _name = "import.lot.serial.wizard"
    _description = "Import Lot/Serial Number Wizard"

    file = fields.Binary(string="File To Import", required=1)

    def normalize_datetime(self, date_value):
        """ Convert date format to '%Y-%m-%d %H:%M:%S' if necessary. Return as is if already in correct format. """
        if not date_value:
            return None  # Skip if no date is provided
        # If the value is already a datetime object, format it correctly
        if isinstance(date_value, datetime.datetime):
            return date_value.strftime("%Y-%m-%d %H:%M:%S")
        date_str = str(date_value)  # Convert to string if not already
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

    def action_import_lot_serial(self):
        """ Create Lot/Serial Numbers through the 'Import' button action """
        try:
            wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)), read_only=True)
            ws = wb.active
            product_obj = self.env["product.product"]
            created_serialnumber = []
            for row in ws.iter_rows(min_row=2):
                # logger.debug(row)
                name = str(row[0].value).strip() if row[0].value else None
                product_name = row[1].value.strip() if row[1].value else None
                create_on = self.normalize_datetime(row[2].value) if row[2].value else None
                company_name = row[3].value.strip() if row[3].value else None
                internal_ref = row[4].value.strip() if row[4].value else None
                location = str(row[5].value).strip() if row[5].value else None
                company_id = self.env['res.company']
                # location_id = self.env['stock.location']
                if name and product_name and create_on:
                    if company_name:
                        company_id = self.env['res.company'].search([('name', 'ilike', company_name)], limit=1)
                    if location and company_name:
                        if '/Stock' in location:
                            # For transfered lot/serial numbers
                            location_id = self.env['stock.location'].search(
                                [('company_id', '=', company_id.id), ('display_name', '=', location)])
                        else:
                            stock_loc = self.env['stock.location'].search(
                                [('company_id', '=', company_id.id), ('name', '=', 'Stock')])
                            location_id = self.env['stock.location'].search(
                                [('company_id', '=', company_id.id), ('name', '=', location),('location_id','=',stock_loc.id)])
                        if not location_id:
                            location_id = self.env['stock.location'].create([{'company_id' : company_id.id,
                                                                         'name': location,
                                                                         'location_id':stock_loc.id}])
                            # raise ValidationError (f'No Location {name}')

                # Get Product
                    product = product_obj.search([('rent_ok', '=', True),('default_code', 'ilike', product_name)], limit=1)
                    if product:
                        product.tracking = 'serial' #changing the product's tracking
                        product.lot_valuated = True
                    else:
                        product_name = product_name.replace(" ", "")
                        product = product_obj.search(
                            [('rent_ok', '=', True), ('default_code', 'ilike', product_name)], limit=1)
                        # product = product_obj.create([{'name': product_name,
                        #                               'type': 'consu',
                        #                               'is_storable':True,}])
                        if not product:
                            raise UserError(f"Product '{product_name}'  in the Lot/Serial Number {name},is not found. Please create it first.")
                    if name and product and location_id:
                        serial_exists = self.env["stock.lot"].search(
                            [('name', 'ilike', name), ('product_id', '=', product.id)])
                        if not serial_exists:
                            new_lot = self.env["stock.lot"].create([{'name': name,
                                                                     'product_id': product.id,
                                                                     'ref': internal_ref if internal_ref else None,
                                                                     'company_id': company_id.id if company_id else None,
                                                                     'location_id': location_id.id if location_id else None}])
                            created_serialnumber.append(new_lot)
                            query = """
                                UPDATE stock_lot
                                SET create_date = %s
                                WHERE id = %s
                            """
                            params = (create_on, new_lot.id)
                            self.env.cr.execute(query, params)
                            self.env["stock.quant"].create([{'location_id': location_id.id,
                                                             'product_id': product.id,
                                                             'lot_id': new_lot.id,
                                                             'inventory_quantity': 1.0}]).action_apply_inventory()
                            stock_quant = self.env["stock.quant"].search([('location_id', '=', location_id.id),
                                                                          ('product_id', '=', product.id),
                                                                          ('lot_id', '=', new_lot.id)])
                            if stock_quant:
                                query = """
                                    UPDATE stock_quant
                                    SET create_date = %s, in_date = %s
                                    WHERE id = %s
                                """
                                params = (create_on, create_on, stock_quant.id)
                                self.env.cr.execute(query, params)
                            stock_valuation_layer = self.env['stock.valuation.layer'].search(
                                                                                    [('company_id', '=', company_id.id),
                                                                                     ('product_id', '=', product.id),
                                                                                     ('lot_id', '=', new_lot.id)])
                            if stock_valuation_layer:
                                query = """
                                    UPDATE stock_valuation_layer
                                    SET create_date = %s
                                    WHERE id = %s
                                    """
                                params = (create_on, stock_valuation_layer.id)
                                self.env.cr.execute(query, params)
                                stock_valuation_layer.stock_move_id.write({'date': create_on})
                                stock_valuation_layer.stock_move_id.move_line_ids.write({'date': create_on})

            # raise ValidationError('success')
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': f"{len(created_serialnumber)} Lot/Serial Numbers Imported Successfully! \n",
                    'type': 'rainbow_man',
                },
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except ValidationError as e:
            raise e