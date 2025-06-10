# -*- coding: utf-8 -*-

from odoo import models, fields


class IncentivesSelection(models.Model):
    _name = 'incentives.selection'
    _description = 'Option Selection'

    name = fields.Char(string="Name", required=True)
