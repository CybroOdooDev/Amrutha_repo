from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        picking = super().button_validate()
        if self.move_ids:
            moves = self.move_ids.filtered(lambda move:move.move_line_ids.lot_id)
            for move in moves:
                move.sale_line_id.write({
                    'rental_pickable_lot_ids':[(6,0,move.move_line_ids.mapped('lot_id').ids)],
                    'actual_delivery_date':fields.Date.today(),
                })
        return picking
