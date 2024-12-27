from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    zoho_record_reference = fields.Char(string='Zoho Record Id',
                                        help='Zoho Record Reference')
