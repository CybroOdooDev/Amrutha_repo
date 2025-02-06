from odoo import models, fields, api,_

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Booleans to enable categories
    enable_residential_sale = fields.Boolean(string="Residential Sale")
    enable_residential_purchase = fields.Boolean(string="Residential Purchase")
    enable_commercial_sale = fields.Boolean(string="Commercial Sale")
    enable_commercial_purchase = fields.Boolean(string="Commercial Purchase")
    enable_auction_sale = fields.Boolean(string="Auction Sale")
    enable_auction_purchase = fields.Boolean(string="Auction Purchase")

    # One2many fields for each category
    residential_sale_docs = fields.One2many(
        'crm.lead.document', 'residential_sale_id', string="Residential Sale Documents"
    )
    residential_purchase_docs = fields.One2many(
        'crm.lead.document', 'residential_purchase_id', string="Residential Purchase Documents"
    )
    commercial_sale_docs = fields.One2many(
        'crm.lead.document', 'commercial_sale_id', string="Commercial Sale Documents"
    )
    commercial_purchase_docs = fields.One2many(
        'crm.lead.document', 'commercial_purchase_id', string="Commercial Purchase Documents"
    )
    auction_sale_docs = fields.One2many(
        'crm.lead.document', 'auction_sale_id', string="Auction Sale Documents"
    )
    auction_purchase_docs = fields.One2many(
        'crm.lead.document', 'auction_purchase_id', string="Auction Purchase Documents"
    )
    # Field to store the count of all documents
    document_count = fields.Integer(string="Documents",
                                    compute='_compute_document_count',
                                    default=0)


    agent_id = fields.Many2one('res.partner',string="Agent")
    seller_buyer_id = fields.Many2one('res.partner',string="Seller/ Buyer")
    transaction_cordinator_id =fields.Many2one('res.users',
                                               string="Transaction Coordinator")
    property_admin_id = fields.Many2one('res.users',string="Property admin")

    def _create_category_documents(self, enable_field, doc_field, lead_field, tag_field):
        """ Helper function to create documents dynamically """
        if getattr(self, enable_field):
            if not self[doc_field]:  # Only create if no documents exist
                templates = self.env['sign.template'].search([
                    ('tag_ids.' + tag_field, '=', True)  # Search within tag_ids
                ])
                documents = [(0, 0, {'name': t.name, 'static_template_id': t.id, 'is_static': True, lead_field: self.id}) for t in templates]
                self.update({doc_field: documents})

    @api.onchange('enable_residential_sale')
    def _onchange_enable_residential_sale(self):
        self._create_category_documents('enable_residential_sale', 'residential_sale_docs', 'residential_sale_id', 'is_residential_sale')

    @api.onchange('enable_residential_purchase')
    def _onchange_enable_residential_purchase(self):
        self._create_category_documents('enable_residential_purchase', 'residential_purchase_docs', 'residential_purchase_id', 'is_residential_purchase')

    @api.onchange('enable_commercial_sale')
    def _onchange_enable_commercial_sale(self):
        self._create_category_documents('enable_commercial_sale', 'commercial_sale_docs', 'commercial_sale_id', 'is_commercial_sale')

    @api.onchange('enable_commercial_purchase')
    def _onchange_enable_commercial_purchase(self):
        self._create_category_documents('enable_commercial_purchase', 'commercial_purchase_docs', 'commercial_purchase_id', 'is_commercial_purchase')

    @api.onchange('enable_auction_sale')
    def _onchange_enable_auction_sale(self):
        self._create_category_documents('enable_auction_sale', 'auction_sale_docs', 'auction_sale_id', 'is_auction_sale')

    @api.onchange('enable_auction_purchase')
    def _onchange_enable_auction_purchase(self):
        self._create_category_documents('enable_auction_purchase', 'auction_purchase_docs', 'auction_purchase_id', 'is_auction_purchase')
    def _compute_document_count(self):
        for lead in self:
            # Count the total documents across all categories
            lead.document_count = len(
                lead.residential_sale_docs.sign_request_id +
                lead.residential_purchase_docs.sign_request_id +
                lead.commercial_sale_docs.sign_request_id +
                lead.commercial_purchase_docs.sign_request_id +
                lead.auction_sale_docs.sign_request_id +
                lead.auction_purchase_docs.sign_request_id
            )

    def action_view_documents(self):
        """ Open the documents view for the current lead """
        self.ensure_one()
        view_id = self.env.ref("sign.sign_request_view_kanban").id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Document Signature Requests'),
            'view_mode': 'kanban',
            'res_model': 'sign.request',
            'domain': [('residential_sale_id', '=', self.id)] +
                      [('residential_purchase_id', '=', self.id)] +
                      [('commercial_sale_id', '=', self.id)] +
                      [('commercial_purchase_id', '=', self.id)] +
                      [('auction_sale_id', '=', self.id)] +
                      [('auction_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def send_all_documents(self):
        print("send all doc ")
        document_records = self.env['crm.lead.document'].search([
            '&', '&',  # Combine AND conditions
            ('is_selected', '=', True),  # First AND condition
            ('is_send', '=', False),  # Second AND condition
            '|', '|', '|', '|', '|',  # Start the OR conditions
            ('residential_sale_id', '=', self.id),
            ('residential_purchase_id', '=', self.id),
            ('commercial_sale_id', '=', self.id),
            ('commercial_purchase_id', '=', self.id),
            ('auction_sale_id', '=', self.id),
            ('auction_purchase_id', '=', self.id),
        ])
        for doc in document_records:
            doc.action_send_for_signature()