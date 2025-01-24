# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SignTemplate(models.Model):
    _inherit = 'sign.template'

    is_crm_template = fields.Boolean(string="Is Crm Template",
                                     help="Template used in CRM document "
                                          "management")