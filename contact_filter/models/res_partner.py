from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def default_get(self, fields_list):
        res = super(Partner, self).default_get(fields_list)
        company_name = self.env.company.name        
        company_id = self.env.company.id
        # Check if it's the specific company you want (replace 1 with your company ID)
        target_company = 'Lange Real Estate'  # Replace with your specific company ID
        
        if company_name == target_company and 'user_id' in fields_list:
            # Get the configured default salesperson for this company
            default_salesperson_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'default_contact_salesperson_id_' + str(company_id), '0'))
            
            if default_salesperson_id > 0:
                res['user_id'] = default_salesperson_id

            # Set default salesperson (e.g., ID 2)
            #res['user_id'] = 2
        return res