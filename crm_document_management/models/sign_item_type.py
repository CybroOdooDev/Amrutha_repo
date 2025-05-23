from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SignItemType(models.Model):
    _inherit = "sign.item.type"
    _description = "Signature Item Type"


    @api.constrains('auto_field')
    def _check_auto_field_exists(self):
        """Ensures that auto_field is a valid field name in crm.lead"""
        lead_model = self.env['crm.lead']  # Reference to crm.lead model
        lead_fields = lead_model._fields  # Get all field names in crm.lead

        for record in self:
            if record.auto_field and record.auto_field not in lead_fields:
                raise ValidationError(_("Invalid field name: %s. It must be a field in crm.lead.") % record.auto_field)
