# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api


class ContractManagementState(models.Model):
    _name = 'contract.management.state'
    _description = 'Contract Management State'
    _order = 'sequence'

    name = fields.Char(required=True, string="State Name")
    sequence = fields.Integer(string="Sequence", default=10)