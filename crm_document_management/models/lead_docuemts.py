from odoo import models, fields, api
from odoo.exceptions import UserError



class CrmLeadDocument(models.Model):
    _name = 'crm.lead.document'
    _description = 'CRM Lead Document'

    name = fields.Char(string="Document Name", required=True)
    stage = fields.Selection([
        ('not_shared', 'Not Shared'),
        ('waiting_signature', 'Waiting on Signature'),
        ('signed', 'Signed'),
    ], string="Stage", default="not_shared", required=True)
    uploaded_file = fields.Binary(
        attachment=True,
        string="PDF File",
        copy=False,
    )
    sign_request_id = fields.Many2one('sign.request', string="Signature Request")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('refused', 'Refused'),
    ], string="Status", default="draft")

    # Relationships with categories
    residential_sale_id = fields.Many2one('crm.lead', string="Residential Sale")
    residential_purchase_id = fields.Many2one('crm.lead', string="Residential Purchase")
    commercial_sale_id = fields.Many2one('crm.lead', string="Commercial Sale")
    commercial_purchase_id = fields.Many2one('crm.lead', string="Commercial Purchase")
    auction_sale_id = fields.Many2one('crm.lead', string="Auction Sale")
    auction_purchase_id = fields.Many2one('crm.lead', string="Auction Purchase")
    template_id= fields.Many2one('sign.template',string="Tempalte")
    is_send= fields.Boolean(default=False)
    is_selected = fields.Boolean(default=False)
    is_agent_signed = fields.Boolean(default=False)
    is_static = fields.Boolean(default=False)
    static_template_id = fields.Many2one('sign.template',string="Template")

    def action_send_for_signature(self):
        """Send documents for signature and move them to 'Waiting on Signature'."""
        for record in self:
            if record.stage != 'not_shared':
                raise UserError(
                    "Only documents in 'Not Shared' stage can be sent for signature.")

            # Determine the correct crm.lead (lead_id)
            lead_id = None
            if self.residential_sale_id:
                lead_id = self.residential_sale_id
            elif self.residential_purchase_id:
                lead_id = self.residential_purchase_id
            elif self.commercial_sale_id:
                lead_id = self.commercial_sale_id
            elif self.commercial_purchase_id:
                lead_id = self.commercial_purchase_id
            elif self.auction_sale_id:
                lead_id = self.auction_sale_id
            elif self.auction_purchase_id:
                lead_id = self.auction_purchase_id
            if not self.is_static:
                # Create the attachment
                attachment = self.env['ir.attachment'].create({
                    'name': "%s.pdf" % self.name,  # File name
                    'type': 'binary',  # Type must be 'binary'
                    'datas': self.uploaded_file,  # Base64-encoded PDF content
                    'mimetype': 'application/pdf',
                    'res_model': 'crm.lead.document',
                    'res_id': self.id,
                })

                # # Find the total number of pages in the uploaded PDF
                # try:
                #     pdf_content = base64.b64decode(self.uploaded_file)  # Decode binary data
                #     pdf_reader = PdfReader(io.BytesIO(pdf_content))  # Read PDF from binary content
                #     total_pages = len(pdf_reader.pages)  # Get the total page count
                # except Exception as e:
                #     raise UserError(f"Error processing the PDF file: {e}")

                # Create the sign template
                template = self.env['sign.template'].create({
                    'name': self.name,
                    'attachment_id': attachment.id,
                })
                self.template_id = template.id

                # Add the signature field to the last page
                pos_y = 0.900  # Default Y position near the bottom of the page
                signature_items = [{
                    'type_id': self.env.ref('sign.sign_item_type_signature').id,
                    'name': lead_id.agent_id.name if lead_id else "Customer Signature",
                    'required': True,
                    'responsible_id': self.env.ref(
                        'sign.sign_item_role_customer').id,
                    'page': 1,  # Dynamically place on the last page
                    'posX': 0.144,  # Default X position
                    'posY': pos_y,
                    'template_id': template.id,
                    'width': 0.2,
                    'height': 0.05,
                }]

                # Create sign items
                self.env['sign.item'].create(signature_items)
            else:
                template = self.static_template_id
                # Check for text fields and validate placeholders
                text_fields = self.env['sign.item'].search([
                    ('template_id', '=', template.id),
                    ('type_id', '=',
                     self.env.ref('sign.sign_item_type_text').id)
                ])
                print(text_fields.name,"name")
                print(text_fields.display_name,"name")

            # Create a sign request
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': record.name,
                'request_item_ids': [(0, 0, {
                    'partner_id': lead_id.agent_id.id if lead_id else None,
                    'role_id': self.env.ref('sign.sign_item_role_customer').id,
                })],
            })

            # Update record fields
            record.sign_request_id = sign_request.id
            record.stage = 'waiting_signature'
            record.status = 'sent'
            record.is_send = True