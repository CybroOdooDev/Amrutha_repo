from odoo import models
from odoo.exceptions import UserError

class CommercialCommissionReport(models.AbstractModel):
    _name = 'report.commission_plan.report_commission'
    _description = 'Commission Report'

    def _get_report_values(self, docids, data=None):
        print("uiuiuiui")
        docs = self.env['crm.lead'].browse(docids)
        for record in docs:
            if not record.date_deadline:
                raise UserError("Please set the Deadline before printing this report.")
            if not record.user_id:
                raise UserError("Please assign a Salesperson before printing this report.")
            if not record.co_agent_user_id:
                raise UserError("Please assign a Co-Agent before printing this report.")
            if not record.total_sales_price:
                raise UserError("Please assign a Sales Price before printing this report.")
            if not record.x_studio_sellerlandlord_name:
                raise UserError("Please assign a Seller before printing this report.")
            if not record.x_studio_buyertenant_name:
                raise UserError("Please assign a Buyer before printing this report.")
            if not record.x_studio_property_address:
                raise UserError("Please set a Property Address before printing this report.")
            if not record.x_studio_opportunity_type_1:
                raise UserError("Please choose a Opportunity type before printing this report.")
            if not record.total_amount:
                raise UserError("Please set value for Total Commission Received by LRE before printing this report.")

        return {
            'doc_ids': docids,
            'doc_model': 'crm.lead',
            'docs': docs,
        }
