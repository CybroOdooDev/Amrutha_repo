# -*- coding: utf-8 -*-

from odoo import fields, models,api


class Lead(models.Model):
    _inherit = 'account.payment'

    lead_id= fields.Many2one('crm.lead')