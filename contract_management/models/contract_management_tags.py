# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ContractManagementTags(models.Model):
    _name = 'contract.management.tags'
    _description = "Contract Management Tags"

    name = fields.Char()
    color = fields.Integer()