# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    is_shelter_company = fields.Boolean(string="Is a Shelter Company")
