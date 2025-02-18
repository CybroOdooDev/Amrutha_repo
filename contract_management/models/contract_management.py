# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class ContractManagement(models.Model):
    _name = 'contract.management'
    _description = "Contract Management"
    _inherit = 'mail.thread'

    name = fields.Char(required=True)
    sequence_test = fields.Integer()
    color = fields.Integer()
    status_id = fields.Many2one('contract.management.state',string="Stage",tracking=True,default=lambda self: self._get_default_status()
                                ,group_expand='_read_group_status_id' ,domain="[]")
    contract_type = fields.Selection([('vendor', 'Vendor'),
                                            ('customer', 'Customer'),
                                            ('internal property', 'Internal-Property'),
                                            ('internal NDA', 'Internal-NDA'),
                                            ('MSA', 'MSA')])
    agreement_application = fields.Selection([('parent only ', 'Parent Only '),
                                      ('parent and subsidiaries', '	Parent and Subsidiaries'),
                                      ('parent and subsidiaries-doc required', 'Parent and Subsidiaries (Affiliate Adoption document required)'),
                                      ('applicable to all parties at location', 'Applicable to all parties at location')],)
    effective_date = fields.Date()
    expiration_date = fields.Date()
    create_date = fields.Date(string="Created On",default=fields.Date.today)
    status = fields.Selection([('active', 'Active'),('expired', 'Expired'),('inactive', 'Inactive')])
    partner_id = fields.Many2one('res.partner')
    partner_phone = fields.Char()
    partner_email = fields.Char()
    user_id = fields.Many2one('res.users')
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id,string="Currency")
    contract_value = fields.Monetary()
    tags = fields.Many2many('contract.management.tags')
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company,)
    notes = fields.Html(translate=True)
    pricing = fields.Boolean()
    rebate = fields.Boolean()
    agreement_only = fields.Boolean()
    details_line_ids = fields.One2many(comodel_name='details.line',inverse_name='contract_id',copy=True, auto_join=True)
    notes = fields.Text('Internal Notes')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked')], string='Kanban State')

    @api.model
    def _get_default_status(self):
        """Setting default status according to sequence"""
        return self.env['contract.management.state'].search([], order='sequence asc', limit=1).id

    @api.model
    def _read_group_status_id(self,stages,domain):
        """Ensure all contract states appear in the Kanban pipeline."""
        # stage_ids = stages.sudo()._search([], order=stages._order)
        # return stages.browse(stage_ids)
        return stages.search([], order='sequence asc')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_test'):
                vals['sequence_test'] = self.env['ir.sequence'].next_by_code(
                    'contract.reference') or 0
        return super().create(vals_list)
