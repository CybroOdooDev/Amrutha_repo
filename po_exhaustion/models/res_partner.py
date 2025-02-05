# -*- coding: utf-8 -*-

from odoo import api,models, fields, Command


class ResPartner(models.Model):
    """To add new fields in the rental order"""
    _inherit = "res.partner"

    po_exhaustion_line = fields.One2many(comodel_name='po.exhaustion', inverse_name='partner_id',
                                        string="PO Exhaustion", copy=True, auto_join=True)