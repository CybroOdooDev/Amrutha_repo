# -*- coding: utf-8 -*-

from odoo import api,fields, models,_
from odoo.exceptions import ValidationError


class RentalRecurringPlan(models.Model):
    _name = 'rental.recurring.plan'
    _description = 'Rental Recurring Plan'
    _inherit = 'mail.thread'


    name = fields.Char(translate=True, required=True, default="Monthly")
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company, required=True, string="Company")

    billing_period_value = fields.Integer(string="Duration", required=True, default=1)
    billing_period_unit = fields.Selection([("days","Days"), ("month", "Months"), ('year', 'Years')],
                                           string="Unit", required=True, default='month')
    billing_period_display = fields.Char(compute='_compute_billing_period_display',string="Billing Period")
    active_rental_count = fields.Integer(compute="_compute_active_rental_count", string="Subscriptions")
    is_default = fields.Boolean()

    @api.depends('billing_period_value', 'billing_period_unit')
    def _compute_billing_period_display(self):
        """To display in the tree view"""
        labels = dict(self._fields['billing_period_unit']._description_selection(self.env))
        for plan in self:
            plan.billing_period_display = f"{plan.billing_period_value} {labels[plan.billing_period_unit]}"

    def _compute_active_rental_count(self):
        """Computing count of rental orders using the plan, for smart button"""
        for record in self:
            record.active_rental_count = self.env['sale.order'].search_count([('recurring_plan_id', 'in', self.ids), ('is_rental_order', '=', True),
             ('state', 'in', ['sent', 'sale'])])

    def action_open_active_rental(self):
        """Smart Button view"""
        return {
            'name': _('Subscriptions'),
            'view_mode': 'list,form',
            'domain': [('recurring_plan_id', 'in', self.ids), ('is_rental_order', '=', True),
                       ('state', 'in', ['sent', 'sale'])],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('is_default')
    def _onchange_is_default(self):
        """ Only one Default Recurirng Plan at a time """
        if self.is_default == True:
            is_default = self.env['rental.recurring.plan'].search([('is_default','=','True')])
            if is_default and is_default.id != self.id:
                raise ValidationError("Already exists a default Recurring Plan")

