# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools import SQL

class RentalSchedule(models.Model):
    _inherit = "sale.rental.schedule"

    delivery_driver = fields.Many2one('res.partner', readonly=False)
    pickup_driver = fields.Many2one('res.partner', readonly=False)

    def _select(self) -> SQL:
        return SQL("""%s,
            prd.delivery_driver as delivery_driver,
            prd.pickup_driver as pickup_driver
        """, super(RentalSchedule, self)._select())

    def _from(self) -> SQL:
        return SQL("""%s
            JOIN product_return_dates prd ON prd.serial_number= lot_info.lot_id
        """, super(RentalSchedule, self)._from())

    def _groupby(self) -> SQL:
        return SQL("""%s,
            prd.delivery_driver,
            prd.pickup_driver
        """, super()._groupby())