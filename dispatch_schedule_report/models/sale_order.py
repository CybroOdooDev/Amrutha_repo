from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one('project.project', string='Project', help='Project')


    def action_confirm(self):
        res = super().action_confirm()
        if self.picking_ids:
            moves =  self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')).move_ids
            print('moves',moves)
            moves_with_lot = moves.filtered(lambda k:k.sale_line_id.rental_pickable_lot_ids)
            print('moves_with_lot',moves_with_lot)
            print('moves_with_lot',moves_with_lot.move_line_ids)
            print('moves_with_lot',moves_with_lot.sale_line_id.rental_pickable_lot_ids)

            for move_lines, lots in zip(moves_with_lot.move_line_ids, moves_with_lot.sale_line_id.rental_pickable_lot_ids):
                print('move_lines',move_lines,lots)
                print('lots',lots)
                move_lines.write({
                    'lot_id':lots.id
                })
            print('linesssssssssssss', moves.move_line_ids)
            for lines in moves.move_line_ids:
                print('lines',lines)
                self.write({
                    'date_records_line': [(0, 0, {
                        'product_id': lines.product_id.id,
                        'serial_number': lines.lot_id.id if lines.lot_id else False,
                        'order_line_id': lines.move_id.sale_line_id.id if lines.move_id.sale_line_id else False,
                        'move_line_id': lines.id if lines else False,
                    })],
                })

        return res


