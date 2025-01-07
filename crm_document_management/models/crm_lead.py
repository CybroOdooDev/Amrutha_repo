from odoo import models, fields, api

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
    seller_buyer_id = fields.Many2one('res.partner',string="Seller/ Buyyer")
    transaction_cordinator_id =fields.Many2one('res.users',
                                               string="Transaction Cordinator")
    property_admin_id = fields.Many2one('res.users',string="Property admin")


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
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lead Documents',
            'view_mode': 'kanban',
            'res_model': 'crm.lead.document',
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