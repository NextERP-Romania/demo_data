# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

import logging
import random
import os
import csv
import codecs
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, models

def days_last_month():
    last_month = date.today() + relativedelta(
        months=-1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    m = last_month.month
    y = last_month.year
    ndays = (date(y, m + 1, 1) - date(y, m, 1)).days
    d1 = date(y, m, 1)
    d2 = date(y, m, ndays)
    delta = d2 - d1
    return [
        (d1 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)
    ]


class RomaniaTestData(models.Model):
    _name = "nexterp.demodata"
    _inherit = "nexterp.demodata.mixin"
    _description = "Create demo data for sale and purchase"

    @api.model
    def install_demo_data(self, company):
        acc_group = self.env.ref("account.group_account_user")
        users = self.env["res.users"].search([])
        for user in users:
            if acc_group and not user.has_group("account.group_account_user"):
                user.write({"groups_id": [(4, acc_group.id)]})
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/"
        )
        f = open(os.path.join(data_dir, "orders.csv"), "rb")
        orders = csv.DictReader(codecs.iterdecode(f, "utf-8"))
        for order in orders:
            if order.get("type") == "sale":
                self.create_sale_order(order)
            elif order.get("type") == "purchase":
                self.create_purchase(order)

    def create_sale_order(self, values):
        if "type" in values:
            values.pop("type")
        if self._context.get("vals", {}):
            values.update(self._context.get("vals", {}))
        values = self.get_references_from_values(values)
        if not values.get("partner_id"):
            values["partner_id"] = self._get_random_customer()
        if not values.get("product_id"):
            prod_type = random.choice(["product", "service"])
            values["product_id"] = self._get_random_product(prod_type)
        partner = values["partner_id"]
        country = partner.country_id
        sale_date = random.choice(days_last_month())
        order_line = [(0, 0, {
                "product_id": values["product_id"].id,
                "product_uom_qty": values.get("product_uom_qty", 1),
                "price_unit": values.get("price_unit", 100),
                "discount": values.get("discount", 0),
            },)
        ]
        fpos = False
        if values.get("fiscal_position_id", False):
            fpos = values["fiscal_position_id"].id
        vals = {
            "partner_id": values["partner_id"].id,
            "partner_invoice_id": values["partner_id"].id,
            "fiscal_position_id": fpos,
            "partner_shipping_id": values["partner_id"].id,
            "currency_id": values.get("currency_id", self.env.company.currency_id).id,
            "create_date": sale_date,
            "date_order": sale_date,
            "validity_date": sale_date,
            "commitment_date": sale_date,
            "effective_date": sale_date,
            "order_line": order_line,
            "client_order_ref": values.get("ref", False),
        }
        notice = values.pop("notice", False)
        avans = values.pop("avans", False)
        sale = self.env["sale.order"].create(vals)
        sale.action_confirm()
        if avans:
            product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            product_id = self.env['product.product'].browse(int(product_id)).exists()
            if product_id:
                adv_wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=[sale.id]).create({
                    'advance_payment_method': 'percentage',
                    'amount': 50.0,
                    'product_id': product_id.id,
                })
                act = adv_wiz.with_context(open_invoices=True).create_invoices()
                invoice = self.env['account.move'].browse(act['res_id'])
                invoice.action_post()
        self.deliver_and_invoice_sales(sale, notice=notice, avans=avans)
        return sale

    def create_purchase(self, values):
        if self._context.get("vals", {}):
            values.update(self._context.get("vals", {}))
        values = self.get_references_from_values(values)
        if not values.get("partner_id"):
            values["partner_id"] = self._get_random_supplier()
        if not values.get("product_id"):
            prod_type = random.choice(["product", "service"])
            values["product_id"] = self._get_random_product(prod_type)
        partner = values["partner_id"]
        country = partner.country_id
        purchase_date = random.choice(days_last_month())
        order_line = [(0, 0, {
                "product_id": values["product_id"].id,
                "product_qty": values.get("product_uom_qty", 1),
                "price_unit": values.get("price_unit", 80)
            },)
        ]
        fpos = False
        if values.get("fiscal_position_id", False):
            fpos = values["fiscal_position_id"].id
        vals = {
            "partner_id": values["partner_id"].id,
            "currency_id": values.get("currency_id", self.env.company.currency_id).id,
            "fiscal_position_id": fpos,
            "create_date": purchase_date,
            "date_order": purchase_date,
            "date_planned": purchase_date,
            "date_approve": purchase_date,
            "effective_date": purchase_date,
            "order_line": order_line,
            "origin": values.get("ref", False)
        }
        notice = values.pop("notice")
        purchase = self.env["purchase.order"].create(vals)
        purchase.onchange_partner_id()
        purchase.button_confirm()
        self.receive_and_invoice_purchases(purchase, notice=notice)
        return purchase

    @api.model
    def receive_and_invoice_purchases(self, purchases, notice=False):
        for purchase in purchases:
            pickings = purchase.picking_ids
            if pickings:
                picking = pickings[0]
                picking.write(
                    {
                        "l10n_ro_notice": notice or False,
                        "scheduled_date": purchase.date_planned,
                        "date_done": purchase.date_planned,
                    }
                )
                for ml in picking.move_line_ids:
                    ml.qty_done = ml.reserved_qty
                picking.button_validate()
                if picking.state == "assigned":
                    picking._action_done()
                if picking.state == "done":
                    action = purchase.action_create_invoice()
                    invoice = self.env["account.move"].browse(action["res_id"])
                    invoice.write(
                        {
                            "date": purchase.date_planned,
                            "invoice_date": purchase.date_planned,
                            "invoice_date_due": purchase.date_planned,
                        }
                    )
                    invoice.action_post()

    @api.model
    def deliver_and_invoice_sales(self, sales, notice=False, avans=False):
        for sale in sales:
            pickings = sale.picking_ids
            if pickings:
                picking = pickings[0]
                picking.write(
                    {
                        "l10n_ro_notice": notice,
                        "create_date": sale.date_order,
                        "scheduled_date": sale.date_order,
                        "date_done": sale.date_order,
                    }
                )
                if picking.state == "draft":
                    picking.action_confirm()
                if picking.state == "waiting":
                    picking.action_assign()
                if picking.state == "assigned":
                    for ml in picking.move_line_ids:
                        ml.qty_done = ml.reserved_qty
                    picking._action_done()
                if picking.state == "done":
                    invoices = sale._create_invoices(final=avans)
                    invoices.write(
                        {
                            "invoice_date": sale.date_order,
                            "invoice_date_due": sale.date_order,
                        }
                    )
                    invoices.action_post()
