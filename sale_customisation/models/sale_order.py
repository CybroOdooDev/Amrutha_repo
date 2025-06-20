from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    is_shelter = fields.Boolean(
        string="Shelter Tab",
        related='company_id.is_shelter_company',
        readonly=False,
    )

    def _compute_is_company_redguard(self):
        for order in self:
            if order.company_id.name == 'RedGuard':
                order.is_company_redguard = True
            else:
                order.is_company_redguard = False

    def _compute_is_company_rdgs(self):
        for order in self:
            main_company = self.env['res.company'].sudo().search([('name', '=', 'RedGuard Diversified Structures')])
            all_company_ids = [main_company.id] + main_company.child_ids.ids
            # if order.company_id.name == 'RedGuard Diversified Structures':
            if order.company_id.id in all_company_ids:
                order.is_company_rdgs = True
            else:
                order.is_company_rdgs = False


    order_status =  fields.Selection([('Awaiting PO','Awaiting PO'),
                              ('PO Received','PO Received'),
                              ('Unit Assignment Ready','Unit Assignment Ready'),
                              ('Service Ready','Service Ready'),], string='Order Status', default='Awaiting PO',tracking=1)
    po_received = fields.Boolean('PO Received', default=False)
    product_family = fields.Selection([('SAS - RESI','SAS - RESI'),('SAS - COMM','SAS - COMM')])
    serial_number = fields.Char('Serial No.')
    adequate_photos_received = fields.Boolean('Adequate Photos Received', default=False)
    install_status = fields.Selection([
        ('awaiting_site_photos', 'Awaiting Site Photos'),
        ('Cancelled', 'Cancelled'),
        ('Customer Awaiting Initial Call', 'Customer Awaiting Initial Call'),
        ('Delivered', 'Delivered'),
        ('Hold for more information', 'Hold for more information'),
        ('Hold Per Customer Request', 'Hold Per Customer Request'),
        ('Installed', 'Installed'),
        ('Ready for delivery', 'Ready for delivery'),
        ('Ready for Install', 'Ready for Install'),
        ('Scheduled install date', 'Scheduled install date'),
        ('Shipped to customer', 'Shipped to customer'),
        ('Shipped to Customer - Hotshot', 'Shipped to Customer - Hotshot'),
        ('Shipped to Customer - Old Dominion',
         'Shipped to Customer - Old Dominion'),
        ('Trying to reach customer', 'Trying to reach customer'),
        ('Unit in production', 'Unit in production'),
        ('Waiting on production', 'Waiting on production'),
    ], string='Install Status', default='awaiting_site_photos')
    installer = fields.Char('Installer')
    pre_install_photos = fields.Boolean('Pre Install Photo(s)')
    installation_notes = fields.Text('Installation Notes')
    est_installation_date = fields.Date('Est. Install Date')
    actual_install_dare = fields.Date('Actual Install Date')
    is_company_redguard = fields.Boolean('Is company Redguard', default=False,
                                        compute='_compute_is_company_redguard')
    is_company_rdgs = fields.Boolean('Is company RDGS', default=False,
                                         compute='_compute_is_company_rdgs')
