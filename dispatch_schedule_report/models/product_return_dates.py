import io
import datetime
from ast import literal_eval
from odoo import api, fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProductReturnDates(models.Model):
    _inherit = 'product.return.dates'

    order_line_id = fields.Many2one('sale.order.line', 'Order Line')
    move_line_id = fields.Many2one('stock.move.line', 'Move Line')
    product_lines = fields.Char('Product Lines',
                                related='product_id.product_line_category',
                                store=True)
    project_id = fields.Many2one('project.project', 'Project',
                                 related='order_id.project_id',
                                 store=True)
    requested_delivery_date = fields.Date('Requested Delivery Date',
                                          related='order_line_id.requested_delivery_date',
                                          help='Requested Delivery Date',
                                          store=True)
    projected_delivery_date = fields.Datetime('Projected Delivery Date',
                                              related='order_line_id.projected_delivery_date',
                                              store=True,
                                              help='Projected Delivery Date')
    projected_pickup_date = fields.Datetime('Projected Pickup Date',
                                            related='order_line_id.projected_pickup_date',
                                            store=True,
                                            help='Projected Pickup Date')
    projected_return_date = fields.Datetime('Projected Return Date',
                                            related='order_line_id.projected_return_date',
                                            store=True,
                                            help='Projected Return Date')
    stop_rent = fields.Date('Stop Rent', help='Stop Rent',
                            related='order_line_id.stop_rent', store=True, )
    delivery_departure_date = fields.Datetime('Delivery Departure Date',
                                              related='order_line_id.delivery_departure_date',
                                              store=True,
                                              help='Delivery Departure Date')
    comment = fields.Text('Comment', related='order_line_id.comment',
                          store=True, )
    door_direction = fields.Char('Door Direction', help='Door Direction',
                                 related='order_line_id.door_direction',
                                 store=True, )
    warehouse_id = fields.Many2one('stock.warehouse',
                                   related='serial_number.location_id.warehouse_id',
                                   string='Warehouse')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 related='order_id.partner_id',
                                 store=True, )
    delivery_address = fields.Char('Delivery Address',
                                   related='order_id.partner_id.contact_address')
    delivery_city = fields.Char('Delivery City',
                                related='order_id.partner_id.city')
    delivery_state_id = fields.Many2one('res.country.state',
                                        help='Delivery State',
                                        related='order_id.partner_id.state_id')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                   related='order_id.pricelist_id')
    actual_delivery_date = fields.Date('Actual Delivery Date')
    is_rental_order = fields.Boolean('Is Rental Order', related='order_id.is_rental_order', store=True)
    company_id = fields.Many2one('res.company', related='order_id.company_id', store=True)

    def get_xlsx_report(self, response):
        # Fetch dispatch companies
        dispatch_companies = self.env['ir.config_parameter'].sudo().get_param(
            'dispatch_schedule_report.dispatch_schedule_company_ids')
        if dispatch_companies:
            dispatch_companies = literal_eval(dispatch_companies) if isinstance(
                dispatch_companies, str) else []
        else:
            dispatch_companies = []

        # domain = [('company_id', 'in',
        #            dispatch_companies)] if dispatch_companies else []

        # Get Deliveries & Pickups
        deliveries = self.env['product.return.dates'].search(
            [('actual_delivery_date', '=', False),
             ('company_id', 'in', dispatch_companies)])
        pickups = self.env['product.return.dates'].search(
            [('return_date', '=', False),
             ('company_id', 'in', dispatch_companies)])
        # Create an in-memory XLSX file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Deliveries")
        sheet2 = workbook.add_worksheet('Pickups')

        # Define column headers
        delivery_headers = ["Product Line", "Project", "Order",
                            "Requested Delivery Date",
                            "Projected Delivery Date",
                            "Delivery Departure Date", "Comment",
                            "Serial Number", "Delivery Driver",
                            "Door Direction",
                            "Warehouse", "Customer", "Delivery Address",
                            "Delivery City", "Delivery State", "Pricelist",
                            "Company"]

        pickup_headers = ["Product Line", "Project #", "Order #", "Stop Rent",
                          "Projected Pickup Date", "Projected Return Date",
                          "Product", "CommentText", "SerialNo",
                          "Pickup Driver", "Return Warehouse", "Shipping Name",
                          "Shipping Address", "Shipping City", "Shipping State",
                          "Price List", 'Company']

        # Apply column widths
        column_widths = [20] * len(delivery_headers)
        for col_num, width in enumerate(column_widths):
            sheet.set_column(col_num, col_num, width)
            sheet2.set_column(col_num, col_num, width)

        # Define header formats
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#F7F7F7', 'border': 1})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        datetime_format = workbook.add_format(
            {'num_format': 'yyyy-mm-dd hh:mm:ss'})

        # Write Headers
        for col, header in enumerate(delivery_headers):
            sheet.write(0, col, header, header_format)

        for col, header in enumerate(pickup_headers):
            sheet2.write(0, col, header, header_format)

        def write_date(sheet, row, col, value, format):
            """Write date/datetime values safely."""
            if value:
                try:
                    dt_value = value if isinstance(value, (datetime.date,
                                                           datetime.datetime)) else datetime.datetime.strptime(
                        value,
                        '%Y-%m-%d %H:%M:%S' if ' ' in value else '%Y-%m-%d')
                    sheet.write_datetime(row, col, dt_value, format)
                except Exception as e:
                    print(
                        f"Error converting date for column {col}: {value} → {e}")
                    sheet.write(row, col, str(value))
            else:
                sheet.write(row, col, '')

        # Write Delivery Data
        row = 1
        for sol in deliveries:
            sheet.write(row, 0, sol.product_lines or '')
            sheet.write(row, 1, sol.project_id.name or '')
            sheet.write(row, 2, sol.order_id.name or '')
            write_date(sheet, row, 3, sol.requested_delivery_date, date_format)
            write_date(sheet, row, 4, sol.projected_delivery_date,
                       datetime_format)
            write_date(sheet, row, 5, sol.delivery_departure_date,
                       datetime_format)
            sheet.write(row, 6, sol.comment or '')
            sheet.write(row, 7, sol.serial_number.name or '')
            sheet.write(row, 8, sol.delivery_driver.name or '')
            sheet.write(row, 9, sol.door_direction or '')
            sheet.write(row, 10, sol.warehouse_id.name or '')
            sheet.write(row, 11, sol.partner_id.name or '')
            sheet.write(row, 12, sol.delivery_address or '')
            sheet.write(row, 13, sol.delivery_city or '')
            sheet.write(row, 14, sol.delivery_state_id.name or '')
            sheet.write(row, 15, sol.pricelist_id.name or '')
            sheet.write(row, 16, sol.company_id.name or '')
            row += 1

        # Apply AutoFilter for Deliveries
        sheet.autofilter(0, 0, row - 1, len(delivery_headers) - 1)

        # Write Pickup Data
        row = 1
        for pickup in pickups:
            if pickup.is_rental_order:
                sheet2.write(row, 0, pickup.product_lines or '')
                sheet2.write(row, 1, pickup.project_id.name or '')
                sheet2.write(row, 2, pickup.order_id.name or '')
                write_date(sheet2, row, 3, pickup.stop_rent, date_format)
                write_date(sheet2, row, 4, pickup.projected_pickup_date,
                           datetime_format)
                write_date(sheet2, row, 5, pickup.projected_return_date,
                           datetime_format)
                sheet2.write(row, 6, pickup.product_id.name or '')
                sheet2.write(row, 7, pickup.comment or '')
                sheet2.write(row, 8, pickup.serial_number.name or '')
                sheet2.write(row, 9, pickup.delivery_driver.name or '')
                sheet2.write(row, 10, pickup.warehouse_id.name or '')
                sheet2.write(row, 11, pickup.partner_id.name or '')
                sheet2.write(row, 12, pickup.delivery_address or '')
                sheet2.write(row, 13, pickup.delivery_city or '')
                sheet2.write(row, 14, pickup.delivery_state_id.name or '')
                sheet2.write(row, 15, pickup.pricelist_id.name or '')
                sheet2.write(row, 16, pickup.company_id.name or '')
                row += 1

        # Apply AutoFilter for Pickups
        sheet2.autofilter(0, 0, row - 1, len(pickup_headers) - 1)

        # Finalize the XLSX file
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
