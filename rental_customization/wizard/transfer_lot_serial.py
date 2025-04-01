# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, _
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
import pytz
from odoo.tools import date_utils


class TransferLotSerialNumberWizard(models.TransientModel):
    _name = "transfer.lot.serial.wizard"
    _description = "Transfer Lot/Serial Number Wizard"

    file = fields.Binary(string="File To Transfer", required=1)

    def action_transfer_lot_serial(self):
        """ Transfer Lot/Serial Numbers through the button action """
        try:
            wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)), read_only=True)
            ws = wb.active
            product_obj = self.env["product.product"]
            for row in ws.iter_rows(min_row=2):
                product_name = str(row[0].value).strip() if row[0].value else None
                name = row[1].value.strip() if row[1].value else None
                company_name = row[2].value.strip() if row[2].value else None
                location = str(row[3].value).strip() if row[3].value else None
                if company_name:
                    company_id = self.env['res.company'].search([('name', 'ilike', company_name)], limit=1)
                if location and company_name:
                    location_id = self.env['stock.location'].search(
                        [('company_id', '=', company_id.id), ('display_name', '=', location)])
                if name and product_name:
                    product = product_obj.search(['|',('name', 'ilike', product_name),('default_code', 'ilike', product_name)], limit=1)
                    serial_exists = self.env["stock.lot"].search(
                        [('name', 'ilike', name), ('product_id', '=', product.id)])
                    if product and serial_exists:
                        create_on = serial_exists.create_date
                        query = """
                                   UPDATE stock_lot
                                   SET create_date = %s,company_id = %s,location_id = %s
                                   WHERE id = %s
                               """
                        params = (create_on, company_id.id, location_id.id, serial_exists.id)
                        self.env.cr.execute(query, params)

                        stock_quant = self.env["stock.quant"].search(
                            [('location_id', '=', serial_exists.location_id.id),
                             ('product_id', '=', product.id),
                             ('lot_id', '=', serial_exists.id)])
                        if stock_quant:
                            create_on = stock_quant.create_date
                            stock_quant.sudo().write({
                                'location_id': location_id.id
                            })
                            # query = """
                            #            UPDATE stock_quant
                            #            SET create_date = %s, in_date = %s,location_id = %s
                            #            WHERE id = %s
                            #        """
                            params = (create_on, create_on, location_id.id, stock_quant.id)
                            self.env.cr.execute(query, params)
                        stock_valuation_layer = self.env['stock.valuation.layer'].search(
                            [('company_id', '=', serial_exists.company_id.id),
                             ('product_id', '=', product.id),
                             ('lot_id', '=', serial_exists.id),
                             ('create_date','=',create_on)])
                        if stock_valuation_layer:
                            query = """
                                   UPDATE stock_valuation_layer
                                   SET create_date = %s, company_id = %s
                                   WHERE id = %s
                                   """
                            params = (create_on, company_id.id, stock_valuation_layer.id)
                            self.env.cr.execute(query, params)
                            stock_valuation_layer.stock_move_id.write({'date': create_on,
                                                                       'location_dest_id': location_id.id})
                            stock_valuation_layer.stock_move_id.move_line_ids.write({'date': create_on,
                                                                                     'location_dest_id': location_id.id})

        except ValidationError as e:
            raise e