from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_line_category = fields.Char('Product Line')
