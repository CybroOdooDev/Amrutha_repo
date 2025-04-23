# -*- coding: utf-8 -*-
from odoo import api, models, fields, Command


class PriceList(models.Model):
    """To add new fields in the rental order"""
    _inherit = "product.pricelist"

    distance_range_line_ids = fields.One2many(
        comodel_name='distance.range.line',
        inverse_name='pricelist_id',
        string="Distance Range Lines",
        copy=True, auto_join=True)

    company_ids = fields.Many2many('res.company', string="Company Names")

    @api.model
    def generate_pricelists(self):
        """ Creating Price lists through Scheduled action """
        company_id = 8
        company_ids = [7,8]
        pricelists_data = [
            # AUS
            {
                "name": "AUS",
                "rates": [167, 225, 300, 375, 425, 575, 825, 6.3],
                "ranges": [(0, 20), (21, 39), (40, 54), (55, 74), (75, 99), (100, 169), (170, 250), (251, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M28", "price": 117.5},
                    {"product_ref": "PS20", "recurrence_ref": "M28", "price": 112.5},
                    {"product_ref": "PS20DD", "recurrence_ref": "M28", "price": 122.5},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 297.5},
                    {"product_ref": "PS20MC", "recurrence_ref": "M28", "price": 267.5},
                    {"product_ref": "PS20OS", "recurrence_ref": "M28", "price": 150},
                    {"product_ref": "PS40", "recurrence_ref": "M28", "price": 132.5},
                    {"product_ref": "PS40DD", "recurrence_ref": "M28", "price": 142.5},
                    {"product_ref": "PS40HC", "recurrence_ref": "M28", "price": 172.5},
                    {"product_ref": "PS40M", "recurrence_ref": "M28", "price": 397.5},
                    {"product_ref": "PS40MC", "recurrence_ref": "M28", "price": 367.5},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M28", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M28", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M28", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M28", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M28", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST48102", "recurrence_ref": "M28", "price": 215},
                    {"product_ref": "ST53102", "recurrence_ref": "M28", "price": 215},
                ]
            },
            # DFW
            {
                "name": "DFW",
                "rates": [167, 225, 300, 375, 425, 575, 825, 6.3],
                "ranges": [(0, 20), (21, 39), (40, 54), (55, 74), (75, 99), (100, 169), (170, 250), (251, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M28", "price": 117.5},
                    {"product_ref": "PS20", "recurrence_ref": "M28", "price": 102.5},
                    {"product_ref": "PS20DD", "recurrence_ref": "M28", "price": 112.5},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 297.5},
                    {"product_ref": "PS20MC", "recurrence_ref": "M28", "price": 267.5},
                    {"product_ref": "PS20OS", "recurrence_ref": "M28", "price": 150},
                    {"product_ref": "PS40", "recurrence_ref": "M28", "price": 122.5},
                    {"product_ref": "PS40DD", "recurrence_ref": "M28", "price": 132.5},
                    {"product_ref": "PS40HC", "recurrence_ref": "M28", "price": 162.5},
                    {"product_ref": "PS40M", "recurrence_ref": "M28", "price": 397.5},
                    {"product_ref": "PS40MC", "recurrence_ref": "M28", "price": 367.5},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M28", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M28", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M28", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M28", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M28", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST48102", "recurrence_ref": "M28", "price": 205},
                    {"product_ref": "ST53102", "recurrence_ref": "M28", "price": 205},
                ]
            },
            # GRN
            {
                "name": "GRN",
                "rates": [6.3],
                "ranges": [(0, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M30", "price": 110},
                    {"product_ref": "PS20", "recurrence_ref": "M30", "price": 110},
                    {"product_ref": "PS20DD", "recurrence_ref": "M30", "price": 120},
                    {"product_ref": "PS20HC", "recurrence_ref": "M30", "price": 130},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 320},
                    {"product_ref": "PS20MC", "recurrence_ref": "M30", "price": 290},
                    {"product_ref": "PS40", "recurrence_ref": "M30", "price": 130},
                    {"product_ref": "PS40DD", "recurrence_ref": "M30", "price": 140},
                    {"product_ref": "PS40HC", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "PS40HCDD", "recurrence_ref": "M30", "price": 155},
                    {"product_ref": "PS40M", "recurrence_ref": "M30", "price": 420},
                    {"product_ref": "PS40MC", "recurrence_ref": "M30", "price": 350},
                    {"product_ref": "PS45HC", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "PS48HC", "recurrence_ref": "M30", "price": 160},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBBIZFEE", "recurrence_ref": "M30", "price": 2},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M30", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M30", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M30", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M30", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M30", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST4596", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "ST48102", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "ST53102", "recurrence_ref": "M30", "price": 175},
                ]
            },
            # ICT
            {
                "name": "ICT",
                "rates": [150, 180, 235, 315, 425, 730, 1050, 6.3],
                "ranges": [(0, 20), (21, 39), (40, 54), (55, 74), (75, 99), (100, 169), (170, 250), (251, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M28", "price": 130},
                    {"product_ref": "PS20", "recurrence_ref": "M28", "price": 130},
                    {"product_ref": "PS20DD", "recurrence_ref": "M28", "price": 140},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 310},
                    {"product_ref": "PS20MC", "recurrence_ref": "M28", "price": 280},
                    {"product_ref": "PS20OS", "recurrence_ref": "M28", "price": 150},
                    {"product_ref": "PS40", "recurrence_ref": "M28", "price": 165},
                    {"product_ref": "PS40DD", "recurrence_ref": "M28", "price": 175},
                    {"product_ref": "PS40HC", "recurrence_ref": "M28", "price": 175},
                    {"product_ref": "PS40M", "recurrence_ref": "M28", "price": 410},
                    {"product_ref": "PS40MC", "recurrence_ref": "M28", "price": 380},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M28", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M28", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M28", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M28", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M28", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST48102", "recurrence_ref": "M28", "price": 205},
                    {"product_ref": "ST53102", "recurrence_ref": "M28", "price": 205},
                ]
            },
            # NEKS
            {
                "name": "NEKS",
                "rates": [150, 180, 230, 315, 425, 730, 1050, 6.3],
                "ranges": [(0, 20), (21, 39), (40, 54), (55, 74), (75, 99), (100, 169), (170, 250), (251, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M28", "price": 130},
                    {"product_ref": "PS20", "recurrence_ref": "M28", "price": 130},
                    {"product_ref": "PS20DD", "recurrence_ref": "M28", "price": 140},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 310},
                    {"product_ref": "PS20MC", "recurrence_ref": "M28", "price": 280},
                    {"product_ref": "PS20OS", "recurrence_ref": "M28", "price": 150},
                    {"product_ref": "PS40", "recurrence_ref": "M28", "price": 165},
                    {"product_ref": "PS40DD", "recurrence_ref": "M28", "price": 175},
                    {"product_ref": "PS40HC", "recurrence_ref": "M28", "price": 175},
                    {"product_ref": "PS40M", "recurrence_ref": "M28", "price": 410},
                    {"product_ref": "PS40MC", "recurrence_ref": "M28", "price": 380},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M28", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M28", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M28", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M28", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M28", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST48102", "recurrence_ref": "M28", "price": 205},
                    {"product_ref": "ST53102", "recurrence_ref": "M28", "price": 205},
                ]
            },
            # OKC
            {
                "name": "OKC",
                "rates": [150, 180, 265, 310, 495, 795, 1325, 6.3],
                "ranges": [(0, 20), (21, 39), (40, 54), (55, 74), (75, 99), (100, 169), (170, 250), (251, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M28", "price": 120},
                    {"product_ref": "PS20", "recurrence_ref": "M28", "price": 120},
                    {"product_ref": "PS20DD", "recurrence_ref": "M28", "price": 130},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 335},
                    {"product_ref": "PS20MC", "recurrence_ref": "M28", "price": 295},
                    {"product_ref": "PS20OS", "recurrence_ref": "M28", "price": 150},
                    {"product_ref": "PS40", "recurrence_ref": "M28", "price": 135},
                    {"product_ref": "PS40DD", "recurrence_ref": "M28", "price": 145},
                    {"product_ref": "PS40HC", "recurrence_ref": "M28", "price": 165},
                    {"product_ref": "PS40M", "recurrence_ref": "M28", "price": 395},
                    {"product_ref": "PS40MC", "recurrence_ref": "M28", "price": 335},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M28", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M28", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M28", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M28", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M28", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST48102", "recurrence_ref": "M28", "price": 205},
                    {"product_ref": "ST53102", "recurrence_ref": "M28", "price": 205},
                ]
            },
            # WTR
            {
                "name": "WTR",
                "rates": [6.3],
                "ranges": [(0, 0)],
                "products": [
                    {"product_ref": "PS10", "recurrence_ref": "M30", "price": 110},
                    {"product_ref": "PS20", "recurrence_ref": "M30", "price": 110},
                    {"product_ref": "PS20DD", "recurrence_ref": "M30", "price": 120},
                    {"product_ref": "PS20HC", "recurrence_ref": "M30", "price": 130},
                    {"product_ref": "PS20M", "recurrence_ref": "M28", "price": 320},
                    {"product_ref": "PS40", "recurrence_ref": "M30", "price": 130},
                    {"product_ref": "PS40DD", "recurrence_ref": "M30", "price": 140},
                    {"product_ref": "PS40HC", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "PS40HCDD", "recurrence_ref": "M30", "price": 155},
                    {"product_ref": "PS40M", "recurrence_ref": "M30", "price": 420},
                    {"product_ref": "RE20", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "RE30", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "SBLOSSWAV-20OF", "recurrence_ref": "M30", "price": 30},
                    {"product_ref": "SBLOSSWAV-40OF", "recurrence_ref": "M30", "price": 40},
                    {"product_ref": "SBLOSSWAV-STCO", "recurrence_ref": "M30", "price": 15},
                    {"product_ref": "SBLOSSWAV-STTR", "recurrence_ref": "M30", "price": 25},
                    {"product_ref": "SBLOT", "recurrence_ref": "M30", "price": 20},
                    {"product_ref": "SBLTOSACQ", "recurrence_ref": "M28", "price": 0},
                    {"product_ref": "ST4596", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "ST48102", "recurrence_ref": "M30", "price": 150},
                    {"product_ref": "ST53102", "recurrence_ref": "M30", "price": 175},
                ]
            },
        ]
        # Fetch applicable products
        product_ids = self.env["product.template"].search([
            ("company_id", "=", company_id),
            ('charges_ok', '=', True),
            ('service_category', 'in', ['delivery', 'pickup'])
        ]).ids
        if not product_ids:
            product_ids = self.env["product.template"].search([
                ("company_id", "=", 6),
                ('charges_ok', '=', True),
                ('service_category', 'in', ['delivery', 'pickup'])
            ]).ids
            if not product_ids:
                return
        for pricelist_data in pricelists_data:
            pricelist_name = pricelist_data["name"]
            rates = pricelist_data["rates"]
            distance_ranges = pricelist_data["ranges"]
            product_pricing = pricelist_data["products"]
            # Find or create the pricelist
            pricelist = self.env["product.pricelist"].search([
                ("name", "=", pricelist_name),
                ("company_ids", "=", company_ids)
            ], limit=1)
            if not pricelist:
                pricelist = self.create([{
                    "name": pricelist_name,
                    "currency_id": self.env.ref("base.USD").id,
                    "company_id": False,
                    "company_ids": company_ids,
                    "active": True,
                }])
            # Fetch existing distance range lines for this pricelist
            existing_lines = self.env["distance.range.line"].search([
                ("pricelist_id", "=", pricelist.id)
            ])
            for i, (distance_begin, distance_end) in enumerate(distance_ranges):
                rate = rates[i]

                # Check if this distance range exists
                existing_line = existing_lines.filtered(
                    lambda line: line.distance_begin == distance_begin and line.distance_end == distance_end
                )

                # Update existing range line
                if existing_line:
                    existing_line.write({"name": [(6, 0, product_ids)],
                                         "transportation_rate": rate, })
                else:
                    self.env["distance.range.line"].create([{
                        "pricelist_id": pricelist.id,
                        "name": [(6, 0, product_ids)],
                        "distance_begin": distance_begin,
                        "distance_end": distance_end,
                        "transportation_rate": rate,
                    }])

            # Add product-specific pricing
            for product_data in product_pricing:
                product = self.env["product.template"].search([
                    ("default_code", "=", product_data["product_ref"])
                ], limit=1)

                recurrence = self.env["sale.temporal.recurrence"].search([
                    ("name", "=", product_data["recurrence_ref"])
                ], limit=1)

                if product and recurrence:
                    price = product_data["price"]

                    pricing_entry = self.env["product.pricing"].search([
                        ("pricelist_id", "=", pricelist.id),
                        ("product_template_id", "=", product.id),
                        ("recurrence_id", "=", recurrence.id)
                    ], limit=1)

                    if pricing_entry:
                        pricing_entry.write({"price": price})
                    else:
                        self.env["product.pricing"].create([{
                            "pricelist_id": pricelist.id,
                            "product_template_id": product.id,
                            "recurrence_id": recurrence.id,
                            "price": price,
                        }])
