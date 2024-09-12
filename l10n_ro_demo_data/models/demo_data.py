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
from odoo.tests import Form

_logger = logging.getLogger(__name__)

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
    def install_demo_data(self, company=False):
        self = self.with_company(company or self.env.company)
        user_group_id = self.env['ir.model.data']._xmlid_to_res_id('base.group_user')
        internal_users = self.env["res.users"].search([]).filtered_domain([('groups_id', 'in', [user_group_id])])
        acc_group = self.env.ref("account.group_account_user")
        acc_aut_group = self.env.ref("stock_account.group_stock_accounting_automatic")
        for user in internal_users:
            if acc_group and not user.has_group("account.group_account_user"):
                user.write({"groups_id": [(4, acc_group.id)]})
            if acc_aut_group and not user.has_group("stock_account.group_stock_accounting_automatic"):
                user.write({"groups_id": [(4, acc_aut_group.id)]})
    @api.model
    def configure_product_categories(self, company):
        categs = [
            ("l10n_ro_demo_data.category_servicii", "service"),
            ("l10n_ro_demo_data.category_materii_prime", "materii_prime"), 
            ("l10n_ro_demo_data.category_produse_finite", "produse_finite"), 
            ("l10n_ro_demo_data.category_marfuri", "marfuri"),
            ("l10n_ro_demo_data.category_marfuri_avg", "marfuri"),
            ("l10n_ro_demo_data.category_ambalaje", "ambalaje"),
            ("l10n_ro_demo_data.category_combustibil", "combustibil"),
            ("l10n_ro_demo_data.category_consumabile", "consumabile"),
        ]
        for categ in categs:
            self.update_test_record_product_category(
                self.env.ref(categ[0]).with_company(company), categ[1])

    @api.model
    def create_demo_data_orders(self, company=False):
        self = self.with_company(company or self.env.company)
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
        order_type = values.pop("type", False)
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
                "product_uom_qty": values.get("qty", 1),
                "price_unit": values.get("price", 100),
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
        sale = self.env["sale.order"].create(vals)
        sale.action_confirm()
        if values.get("advance") != "0":
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
        self.deliver_and_invoice_sales(sale, values)
        return sale

    @api.model
    def deliver_and_invoice_sales(self, sales, values):
        order_type = values.pop("type", False)
        for sale in sales:
            pickings = sale.picking_ids
            if pickings:
                picking = pickings[0]
                picking.write(
                    {
                        "l10n_ro_notice": values.get("notice") == "1",
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
                    for move in picking.move_ids:
                        move._set_quantity_done(sum(ml.quantity for ml in move.move_line_ids))
                    picking._action_done()
                if picking.state == "done":
                    invoices = sale._create_invoices(final=True)
                    invoice_line = invoices[0].invoice_line_ids[0]
                    invoice_line.write(
                        {
                            "quantity": float(values.get("qty")),
                            "price_unit": float(values.get("inv_price"))
                        }
                    )
                    invoices.write(
                        {
                            "invoice_date": sale.date_order,
                            "invoice_date_due": sale.date_order,
                        }
                    )
                    invoices.action_post()

    def create_purchase(self, values):
        order_type = values.pop("type", False)
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
                "product_qty": values.get("qty", 1),
                "price_unit": values.get("price", 80)
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
        purchase = self.env["purchase.order"].create(vals)
        purchase.onchange_partner_id()
        purchase.button_confirm()
        if values.get("reception_in_progress") != "0":
            purchase.action_create_reception_in_progress_invoice()
            invoice = purchase.invoice_ids[0]
            invoice.write(
                {
                    "date": purchase.date_order,
                    "invoice_date": purchase.date_order,
                    "invoice_date_due": purchase.date_order,
                }
            )
            invoice.action_post()
        self.receive_and_invoice_purchases(purchase, values)
        if values.get("step") == "2":
            self.with_context(step=2).receive_and_invoice_purchases(purchase, values)
        return purchase

    @api.model
    def receive_and_invoice_purchases(self, purchases, values):
        order_type = values.pop("type", False)
        step = self.env.context.get("step", 1)
        for purchase in purchases:
            picking = self.env["stock.picking"]
            if step == 2 and float(values.get("stock_qty2")) < 0:
                # Create return to initial reception
                picking = purchase.picking_ids.filtered(lambda x: x.state == "done")
                if picking:
                    stock_return_picking_form = Form(
                        self.env["stock.return.picking"].with_context(
                            active_ids=picking.ids, active_id=picking.ids[0], active_model="stock.picking"
                        )
                    )
                    return_wiz = stock_return_picking_form.save()
                    return_wiz.product_return_moves.write({"quantity": -1 * float(values.get("stock_qty2")), "to_refund": True})
                    res = return_wiz.create_returns()
                    return_pick = self.env["stock.picking"].browse(res["res_id"])
                    return_pick.action_confirm()
                    return_pick.action_assign()
                    for move in return_pick.move_ids:
                        move._set_quantity_done(-1 * float(values.get("stock_qty2")))
                    return_pick._action_done()
                    picking = return_pick
            else:
                # Create reception
                pickings = purchase.picking_ids.filtered(lambda x: x.state != "done")
                if pickings:
                    picking = pickings[0]
                    picking.write(
                        {
                            "l10n_ro_notice": values.get("notice") == "1",
                            "scheduled_date": purchase.date_planned,
                            "date_done": purchase.date_planned,
                        }
                    )
                    qty_done = float(values.get("stock_qty") if step == 1 else values.get("stock_qty2"))
                    
                    for move in picking.move_ids:
                        move._set_quantity_done(qty_done)
                    picking.button_validate()
                    if picking.state == "assigned":
                        picking._action_done()
            if picking.state == "done":
                invoice = self.env["account.move"]
                try:
                    action = purchase.action_create_invoice()
                    invoice = self.env["account.move"].browse(action["res_id"])
                except Exception as e:
                    _logger.info("Error creating invoice: %s" % e)
                if invoice:
                    invoice_line = invoice.invoice_line_ids[0]
                    inv_qty = values.get("inv_qty") if step == 1 else values.get("inv_qty2")
                    inv_price = values.get("inv_price") if step == 1 else values.get("inv_price2")
                    invoice_line.write(
                        {
                            "quantity": float(inv_qty),
                            "price_unit": float(inv_price)
                        }
                    )
                    if values.get("landed_cost") != "0":
                        self.create_landed_cost(invoice, picking, values)
                    invoice.write(
                        {
                            "date": purchase.date_planned,
                            "invoice_date": purchase.date_planned,
                            "invoice_date_due": purchase.date_planned,
                        }
                    )
                    if invoice.amount_total < 0:
                        invoice.action_switch_invoice_into_refund_credit_note()
                    invoice.with_context(
                        l10n_ro_approved_price_difference=True
                    ).action_post()

    def create_landed_cost(self, invoice, picking, values):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id),("type", "=", "general")], limit=1
        )
        product = self.env.ref("l10n_ro_demo_data.nexterp_demo_product_17", raise_if_not_found=False)
        landed_cost = self.env["stock.landed.cost"].create(
            {
                "picking_ids": [(4, picking.id)],
                "vendor_bill_id": invoice.id,
                "account_journal_id": journal.id,
                "date": invoice.date,
                "cost_lines": [
                    (0, 0, {
                        "product_id": product.id,
                        "price_unit": float(values.get("landed_cost")),
                        "split_method": "equal",
                        "account_id": product.property_account_expense_id.id,
                        }
                    )
                ],
            }
        )
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()