from ast import literal_eval

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dispatch_schedule_company_ids = fields.Many2many('res.company',
                                                     string="Dispatch Schedule company",
                                                     readonly=False)

    def set_values(self):
        """this function helps to save values in the settings"""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'dispatch_schedule_report.dispatch_schedule_company_ids',
            self.dispatch_schedule_company_ids.ids)
        return res

    @api.model
    def get_values(self):
        """this function retrieve the values from the ir_config_parameters"""
        res = super().get_values()
        dispatch_schedule_company_ids = self.env[
            'ir.config_parameter'].sudo().get_param(
            'dispatch_schedule_report.dispatch_schedule_company_ids')
        res.update(
            dispatch_schedule_company_ids=[
                fields.Command.set(literal_eval(dispatch_schedule_company_ids))
            ] if dispatch_schedule_company_ids else False)

        return res
