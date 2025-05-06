# In a file like models/res_config_settings.py
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_contact_salesperson_id = fields.Many2one(
        'res.users',
        string='Default Salesperson for Contacts',
        help='This user will be set as the default salesperson for new contacts'
    )
    
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update(
            default_contact_salesperson_id=int(self.env['ir.config_parameter'].sudo().get_param(
                'default_contact_salesperson_id_' + str(company.id), '0'))
        )
        return res
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        self.env['ir.config_parameter'].sudo().set_param(
            'default_contact_salesperson_id_' + str(company.id), 
            str(self.default_contact_salesperson_id.id or '0')
        )