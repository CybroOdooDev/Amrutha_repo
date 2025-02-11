from odoo import models, fields, api, _,Command
import base64


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sign_request_ids = fields.Many2many('sign.request',
                                        string='Signature Requests')
    sign_request_count = fields.Integer(compute='_compute_sign_request_count')
    is_signed = fields.Boolean(string="Is Approved",compute='_compute_is_signed')
    signed_document = fields.Many2one('ir.attachment',)
    is_attached = fields.Boolean(string="Proof Attached",default=False)
    is_invoice_created =fields.Boolean(string="Invoice created",
                                       default=False, readonly=True)

    @api.depends('sign_request_ids')
    def _compute_sign_request_count(self):
        for lead in self:
            lead.sign_request_count = len(lead.sign_request_ids)


    @api.depends('sign_request_ids')
    def _compute_is_signed(self):
        print("_compute_is_signed")
        for requests in  self.sign_request_ids:
            if requests.state=='signed':
                self.is_signed = True
                self.signed_document = (
                    self.sign_request_ids.completed_document_attachment_ids)[1]
                if not self.is_attached:
                    body = u"You will find attached the proof of payment document"
                    self.message_post(body=body, attachment_ids=self.sign_request_ids.completed_document_attachment_ids.ids)
                    self.is_attached = True


        else:
            self.is_signed = False

    def create_invoice(self):
        if self.is_attached:
            print("invoice")
            tax = self.env['account.tax'].search(
                [('company_id', '=', self.env.company.id),
                 ('amount', '=', float(0.00)),
                 ('amount_type', '=', 'percent'),
                 ('type_tax_use', '=', 'sale'),
                 ], limit=1)
            self.env['account.move'].create([{
                'move_type': 'in_invoice',
                'partner_id': self.user_id.secondary_related_partner_id.id
                if self.user_id.secondary_related_partner_id else
                self.user_id.partner_id.id,
                'crm_lead_id':self.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.env.ref(
                        'commission_payout_sign.product_commission').id,
                    'price_unit': self.commission_to_be_paid,
                    'quantity': 1,
                    'tax_ids': [Command.set(tax.ids)]
                })]
            }])
            if self.referer_id:
                self.env['account.move'].create([{
                    'move_type': 'in_invoice',
                    'partner_id': self.referer_id.id,
                    'crm_lead_id': self.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': self.env.ref(
                            'commission_payout_sign.product_referral').id,
                        'price_unit': self.referral_fee,
                        'quantity': 1,
                        'tax_ids': [Command.set(tax.ids)]
                    })]
                }])
            if self.inside_sale_person_id:
                self.env['account.move'].create([{
                    'move_type': 'in_invoice',
                    'partner_id':  self.inside_sale_person_id.secondary_related_partner_id.id if self.inside_sale_person_id.secondary_related_partner_id else self.inside_sale_person_id.partner_id.id,
                    'crm_lead_id': self.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': self.env.ref(
                            'commission_payout_sign.product_inside_sale').id,
                        'price_unit': self.inside_sale_fee,
                        'quantity': 1,
                        'tax_ids': [Command.set(tax.ids)]
                    })]
                }])
            self.is_invoice_created = True

    def action_get_commission_invoice_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Commission Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': "{'create': False}"
        }


    def action_open_sign_requests(self):
        """Open the signature requests related to the lead."""
        self.ensure_one()

        responsible_ids = self.env['sign.item.role']
        print(responsible_ids,"responsible_ids")

        # Signature requests directly linked to the lead
        direct_sign_requests = self.sign_request_ids

        # Collect signature requests related to required approvers (using customer role)
        role_sign_requests = self.env['sign.request'].browse([])
        if self.required_approvers:
            role_sign_requests = self.env['sign.request.item'].search([
                ('partner_id', 'in', self.required_approvers.ids),
                ('role_id', '=',
                 self.env.ref('sign.sign_item_role_customer').id)
            ]).mapped('sign_request_id')

        # Combine all signature requests
        sign_request_ids = direct_sign_requests | role_sign_requests

        # Open directly if there is only one signature request
        if len(sign_request_ids.ids) == 1:
            return sign_request_ids.go_to_document()

        # Determine view ID based on user group (if applicable)
        if self.env.user.has_group('sign.group_sign_user'):
            view_id = self.env.ref("sign.sign_request_view_kanban").id
        else:
            view_id = self.env.ref(
                "custom_module.sign_request_view_kanban_custom").id

        # Return action to show the signature requests
        return {
            'type': 'ir.actions.act_window',
            'name': _('Signature Requests'),
            'view_mode': 'kanban,tree',
            'res_model': 'sign.request',
            'view_ids': [(view_id, 'kanban'), (False, 'tree')],
            'domain': [('id', 'in', sign_request_ids.ids)],
        }

    def action_signature_request_wizard(self):
        """Open the signature request wizard."""
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'commission_payout_sign.sign_document_wizard_action')
        partner_ids = []

        # Loop through each partner in self.required_approvers (which is a Many2many field)
        for partner in self.required_approvers:
            partner_ids.append(
                partner.id)  # Append the partner's ID to the list
        action['context'] = {
            'default_crm_lead_id': self.id,
            'default_sign_template_id': self.create_signature_template(),
            'default_partner_ids': partner_ids
        }
        return action

    @api.model
    def create_signature_template(self):
        # Create a sign request template
        template = self.env['sign.template'].create({
            'name': self.name,
            'attachment_id': self.commission_attachment_id.id,
        })
        # Initialize a list to hold the signature items
        signature_items = []

        # Loop through each approver in self.required_approvers
        pos_y = 0.900  # Starting vertical position
        padding = 0.05  # Space between signature boxes

        for approver in self.required_approvers:
            signature_items.append({
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                # Signature item type
                'name': approver.name,  # No specific name for signature fields
                'required': True,  # Mark the field as required
                'responsible_id': self.env.ref(
                    'commission_payout_sign.sign_item_role_commission_approve').id,
                # Role for customer
                'page': 1,  # Adjust the page number as needed
                'posX': 0.144,  # X position remains constant
                'posY': pos_y,  # Use the dynamic vertical position
                'template_id': template.id,  # Template ID for the sign items
                'width': 0.2,  # Width of the signature box
                'height': 0.05,  # Height of the signature box
            })
            pos_y -= 0.05 + padding  # Move the Y position up for the next box

        # Create the sign items for the template
        self.env['sign.item'].create(signature_items)
        print(signature_items, "signature_items")
        return template.id
