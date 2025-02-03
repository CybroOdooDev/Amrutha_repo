from odoo import models, fields


class Product(models.Model):
   _inherit = 'product.product'

   zoho_reference = fields.Char('Product Zoho reference', help='Product Zoho Reference')
   roof_color = fields.Char('ROOF COLOR',help='ROOF COLOR')
   roof_gauge = fields.Char('ROOF GAUGE',help='ROOF GAUGE')
   brand = fields.Char('BRAND', help='BRAND')
   length = fields.Char('Length', help='Length')
   width = fields.Float('Width', help='Width')
   eve_height = fields.Char('Eve Height',help='Eve Height')
