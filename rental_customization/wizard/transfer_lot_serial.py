# -*- coding: utf-8 -*-

import datetime
from email.policy import default
from odoo import models, fields, api,_
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
import pytz
from odoo.tools import date_utils


class TransferLotSerialNumberWizard(models.TransientModel):
    _name = "transfer.lot.serial.wizard"
    _description = "Transfer Lot/Serial Number Wizard"

    company_id = fields.Integer(default=lambda self: self.env.company.id)
    upload_file = fields.Boolean(string="Upload file to Transfer")
    upload_details = fields.Boolean(string="Upload transfer details here")
    file = fields.Binary(string="File To Transfer", required=1)
    lot_ids = fields.Many2many('stock.lot', domain=lambda self: self._get_lot_domain(),required=True)
    destination_company_id = fields.Many2one('res.company',store=True,domain=lambda self: self._get_company_domain(),required=True)
    location_ids = fields.Many2many('stock.location',store=True,compute="_compute_locations")
    destination_location_id = fields.Many2one('stock.location',domain="[('id', 'in', location_ids)]",required=True)

    def _get_lot_domain(self):
        """Computes domain dynamically to include lots from the current company or no company"""
        return ['|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)]

    def _get_company_domain(self):
        """Computes domain dynamically to include Companies under the same parent company"""
        return ['|',('id','=',self.env.company.parent_id.id),('parent_id', '=', self.env.company.parent_id.id)]

    @api.depends('destination_company_id')
    def _compute_locations(self):
        if self.destination_company_id:
            self.location_ids = [fields.Command.set(self.location_ids.search([('company_id', '=', self.destination_company_id.id)]).ids)]
        else:
            self.location_ids = self.env['stock.location'].search([])

    @api.onchange('upload_file')
    def _onchange_upload_fields(self):
        """To keep only one boolean as True at a time"""
        if self.upload_file :
            self.upload_details = False
            self.upload_file = True

    @api.onchange('upload_details')
    def _onchange_upload_details(self):
        """To keep only one boolean as True at a time"""
        if self.upload_details:
            self.upload_file = False
            self.upload_details = True

    def action_transfer_lot_serial(self):
        """ Transfer Lot/Serial Numbers through the button action """
        if self.upload_file:
            try:
                wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)), read_only=True)
                ws = wb.active
                product_obj = self.env["product.product"]
                for row in ws.iter_rows(min_row=2):
                    lot_name = str(row[0].value).strip() if row[0].value else None
                    product_name = row[1].value.strip() if row[1].value else None
                    destination_company_name = row[2].value.strip() if row[2].value else None
                    destination_location = str(row[3].value).strip() if row[3].value else None
                    current_company = self.env.company
                    if not (lot_name and product_name and destination_company_name and destination_location):
                        break
                    if destination_company_name:
                        destination_company_id = self.env['res.company'].search([('name', '=', destination_company_name)], limit=1)
                    if destination_location and destination_company_name:
                        destination_location_id = self.env['stock.location'].search(
                            [('company_id', '=', destination_company_id.id), ('display_name', '=', destination_location)])
                    if lot_name and product_name:
                        product = product_obj.search(['|',('name', 'ilike', product_name),('default_code', 'ilike', product_name)], limit=1)
                        stock_lot = self.env["stock.lot"].search(
                            [('name', 'ilike', lot_name), ('product_id', '=', product.id)])
                        if  stock_lot.reserved or stock_lot.location_id.name == 'Rental':
                            raise ValidationError(f"The Lot/Serial No.{lot_name} is not yet returned")
                        if product and product.company_id and product.company_id != current_company.parent_id:
                            raise ValidationError(f"The Product ' {product_name} ' is restricted to the branch {product.company_id.name}")
                        if product and stock_lot and stock_lot.company_id != destination_company_id:

                            stock_quant = self.env["stock.quant"].search(
                                [('location_id', '=', stock_lot.location_id.id),
                                 ('product_id', '=', product.id),
                                 ('lot_id', '=', stock_lot.id)])
                            if stock_quant:
                                stock_quant.update({'inventory_quantity': 0})
                                stock_quant.action_apply_inventory()
                                stock_lot.update({'company_id':destination_company_id.id})
                                self.env["stock.quant"].create([{'location_id': destination_location_id.id,
                                                                 'product_id': product.id,
                                                                 'lot_id': stock_lot.id,
                                                                 'inventory_quantity': 1.0}]).action_apply_inventory()
                self.env['sale.order.line']._compute_pickeable_lot_ids()
                            # raise ValidationError('Success')
            except ValidationError as e:
                raise e

        if self.upload_details:
            if self.destination_company_id and self.destination_location_id:
                destination_company_id = self.destination_company_id
                destination_location_id = self.destination_location_id
                current_company = self.company_id
                for lot in self.lot_ids:
                    product_id = lot.product_id
                    if  lot.reserved or lot.location_id.name == 'Rental':
                        raise ValidationError(f"The Lot/Serial No.{lot.name} is not yet returned")
                    if product_id and product_id.company_id and product_id.company_id != current_company.parent_id:
                        raise ValidationError(f"The Product ' {product_id.name} ' is restricted to the branch {product_id.company_id.name}")
                    if product_id and lot and lot.company_id != destination_company_id:
                        stock_quant = self.env["stock.quant"].search(
                            [('location_id', '=', lot.location_id.id),
                             ('product_id', '=', product_id.id),
                             ('lot_id', '=', lot.id)])
                        if stock_quant:
                            stock_quant.update({'inventory_quantity': 0})
                            stock_quant.action_apply_inventory()
                            lot.update({'company_id':destination_company_id.id})
                            self.env["stock.quant"].create([{'location_id': destination_location_id.id,
                                                             'product_id': product_id.id,
                                                             'lot_id': lot.id,
                                                             'inventory_quantity': 1.0}]).action_apply_inventory()
                    self.env['sale.order.line']._compute_pickeable_lot_ids()
                    # raise ValidationError('success')



