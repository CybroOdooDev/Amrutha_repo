# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DetailsLine(models.Model):
    _name = 'details.line'

    contract_id = fields.Many2one(comodel_name='contract.management',
        required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Description')
    contract_begin_date = fields.Date('Execution Date')
    expiration_date = fields.Date('Expiration Date')
    current_revision = fields.Boolean()
    document = fields.Binary()