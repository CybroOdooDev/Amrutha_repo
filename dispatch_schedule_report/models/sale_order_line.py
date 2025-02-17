from odoo import fields, models
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter



class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    requested_delivery_date = fields.Date('Requested Delivery Date',
                                          help='Requested Delivery Date')
    projected_delivery_date = fields.Datetime('Projected Delivery Date',
                                              help='Projected Delivery Date')
    projected_pickup_date = fields.Datetime('Projected Pickup Date',
                                            help='Projected Pickup Date')
    projected_return_date = fields.Datetime('Projected Return Date',
                                            help='Projected Return Date')

    stop_rent = fields.Date('Stop Rent', help='Stop Rent')
    delivery_departure_date = fields.Datetime('Delivery Departure Date',
                                              help='Delivery Departure Date')
    comment = fields.Text('Comment')
    serial_number = fields.Char('Serial Number')
    door_direction = fields.Char('Door Direction', help='Door Direction')
    actual_delivery_date = fields.Date('Actual Delivery Date')

