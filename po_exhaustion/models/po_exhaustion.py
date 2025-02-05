# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api


class ProductReturnDates(models.Model):
    _name = 'po.exhaustion'

    partner_id = fields.Many2one(comodel_name='res.partner',string="Partner Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    po_name = fields.Char("Customer PO",required=True)
    issued_date = fields.Date('Issued Date')
    currency_id = fields.Many2one('res.currency', related='partner_id.company_id.currency_id',readonly=False)
    amount_issued = fields.Monetary()
    total_consumed = fields.Monetary(compute="_compute_total_consumed",)
    total_remaining = fields.Monetary(compute="_compute_total_remaining",)
    notes = fields.Text()
    create_uid = fields.Many2one('res.users',string='Created By',default=lambda self: self.env.user)

    @api.depends('po_name')
    def _compute_total_consumed(self):
        """Compute total invoiced amount of sale orders with matching customer PO"""
        for record in self:
            sale_orders = self.env['sale.order'].search([('customer_po', '=', record.po_name),
                                                         ('partner_id', '=', record.partner_id._origin.id)])
            record.total_consumed = sum(sale_orders.mapped('total_invoiced_amount'))

    @api.depends('amount_issued', 'total_consumed')
    def _compute_total_remaining(self):
        """Compute remaining amount after consumption"""
        for record in self:
            record.total_remaining = record.amount_issued - record.total_consumed

    # @api.depends('po_name')
    # def _compute_total_consumed(self):
    #     """Compute total invoiced amount of sale orders with matching customer PO"""
    #     for record in self:
    #         sale_orders = self.env['sale.order'].search([('customer_po', '=', record.po_name),
    #                                                      ('partner_id', '=', record.partner_id.id)])
    #         if sale_orders:
    #             for order in sale_orders:
    #                 if order.customer_po:
    #                     invoices = order.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'posted'))
    #                     total_invoiced_amount = sum(invoices.mapped('amount_total'))
    #                 else:
    #                     total_invoiced_amount = 0.0
    #                 record.total_consumed += total_invoiced_amount
    #         else:
    #             record.total_consumed = 0