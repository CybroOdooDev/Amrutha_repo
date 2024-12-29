from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError, UserError


class SignDocumentWizard(models.TransientModel):
    _name = 'crm.sign.document.wizard'
    _description = 'Send Signature Request for CRM Lead'

    crm_lead_id = fields.Many2one('crm.lead', string='Lead', required=True,
                                  default=lambda self: self.env.context.get(
                                      'active_id'))
    sign_template_id = fields.Many2one('sign.template',
                                       string='Document Template',
                                       required=True)
    partner_ids = fields.Many2many(
        'res.partner', store=False
    )
    message = fields.Text(string='Message',
                          help='Optional message for the recipient')

    def validate_signature(self):
        self.ensure_one()
        request_items = []
        role = self.env.ref(
            'commission_payout_sign.sign_item_role_commission_approve',
            raise_if_not_found=False)
        if not role:
            raise ValidationError(
                _("The required sign role (Customer) is not configured."))

        for partner in self.crm_lead_id.required_approvers:
            print("partner_id", partner.partner_id)
            request_items.append(
                Command.create({
                    'partner_id': partner.partner_id.id,
                    'role_id': role.id,
                })
            )
        print("request_items", request_items)
        # Check and delete existing sign requests
        if self.crm_lead_id.sign_request_ids:
            self.crm_lead_id.sign_request_ids.unlink()

        # # Create sign request
        # sign_request = self.env['sign.request'].create({
        #     'template_id': self.sign_template_id.id,
        #     'reference': self.sign_template_id.display_name,
        #     'request_item_ids': request_items,
        # })

        for partner in self.crm_lead_id.required_approvers:
            sign_request = self.env['sign.request'].create({
                'template_id': self.sign_template_id.id,
                'reference': self.sign_template_id.display_name,
                'request_item_ids': [Command.create({
                    'partner_id': partner.partner_id.id,
                    'role_id': role.id,
                })],
            })
            self.crm_lead_id.sign_request_ids = [(4, sign_request.id)]
        #
        # recipient_emails = {member.partner_id.email for member in
        #                     self.crm_lead_id.required_approvers if
        #                     member.partner_id.email}
        # if not recipient_emails:
        #     raise UserError(
        #         "Please ensure all required approvers have an email address.")
        # # Convert the set to a comma-separated string
        # recipient_emails_str = ', '.join(recipient_emails)
        #
        # self.env['mail.mail'].sudo().create({
        #     'subject': f"New Signature Request Created: {self.crm_lead_id.name}",
        #     'email_from': self.env.user.login,
        #     'email_to': recipient_emails_str,
        #     'body_html': f"""
        #             <p>Hello Team,</p>
        #
        #             <p>A new Signature Request created in the CRM
        #             system:</p>
        #
        #             <p>Please follow up on this lead as soon as possible.</p>
        #
        #             <p>Best Regards,<br>CRM System</p>
        #         """
        # }).send()
        if len(self.crm_lead_id.sign_request_ids.ids) == 1:
            return self.crm_lead_id.sign_request_ids.go_to_document()
        view_id = self.env.ref("sign.sign_request_view_kanban").id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Signature Requests',
            'view_mode': 'kanban,tree',
            'res_model': 'sign.request',
            'view_ids': [(view_id, 'kanban'), (False, 'tree')],
            'domain': [('id', 'in', self.crm_lead_id.sign_request_ids.ids)]
        }
