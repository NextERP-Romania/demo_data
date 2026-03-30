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
        internal_users = self.env["res.users"].search([]).filtered_domain([('group_ids', 'in', [user_group_id])])
        if not internal_users:
            internal_users = self.env["res.users"].search([("share", "=", False)])
        acc_group = self.env.ref("account.group_account_user")
        for user in internal_users:
            if acc_group and not user.has_group("account.group_account_user"):
                user.write({"groups_id": [(4, acc_group.id)]})

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
    def configure_product_taxes(self, company):
        product_taxes = [
            ('l10n_ro_demo_data.nexterp_demo_product_1', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_2', 'VAT collected 11% Goods', 'VAT deductible 11% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_4', 'VAT collected 0% Goods', 'VAT deductible 0% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_5', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_6', 'VAT collected 11% Goods', 'VAT deductible 11% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_8', 'VAT collected 0% Goods', 'VAT deductible 0% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_9', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_10', 'VAT collected 11% Goods', 'VAT deductible 11% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_12', 'VAT collected 0% Goods', 'VAT deductible 0% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_13', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_14', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_15', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_16', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_17', 'VAT collected 21% Services', 'VAT deductible 21% Services'),
            ('l10n_ro_demo_data.nexterp_demo_product_18', 'VAT collected 21% Services', 'VAT deductible 21% Services'),
            ('l10n_ro_demo_data.nexterp_demo_product_19', 'VAT collected 21% Services', 'VAT deductible 21% Services'),
            ('l10n_ro_demo_data.nexterp_demo_product_20', 'VAT collected 11% Services', 'VAT deductible 11% Services'),
            ('l10n_ro_demo_data.nexterp_demo_product_22', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_23', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_24', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_25', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
            ('l10n_ro_demo_data.nexterp_demo_product_26', 'VAT collected 21% Goods', 'VAT deductible 21% Goods'),
        ]
        for pr_tax in product_taxes:
            product = self.env.ref(pr_tax[0], raise_if_not_found=False)
            if product:
                product = product.with_company(company)
                sale_tax = self.env["account.tax"].search(
                    [("description", "=", pr_tax[1]), ("company_id", "=", company.id)]
                )
                purchase_tax = self.env["account.tax"].search(
                    [("description", "=", pr_tax[2]), ("company_id", "=", company.id)]
                )
                if sale_tax:
                    product.taxes_id = sale_tax
                if purchase_tax:
                    product.supplier_taxes_id = purchase_tax

    @api.model
    def create_demo_data_orders(self, company=False):
        self = self.with_company(company or self.env.company)
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/"
        )
        filename = "orders.csv"
        orders = self.read_orders_from_csv_file(filename, module_dir=data_dir)
        for _key, order in orders.items():
            _logger.info(
                "Import order no: %s - %s", order.get("code"), order.get("name")
            )
            self.import_order(order)

    def read_orders_from_csv_file(self, filename, module_dir=None):
        if not module_dir:
            module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(module_dir, "tests/cases/")
        f = open(os.path.join(data_dir, filename), "rb")
        reader = csv.DictReader(codecs.iterdecode(f, "utf-8"))
        orders_data = {}
        for row in reader:
            if row.get("order_no") not in orders_data:
                row_case = row.copy()
                orders_data[row["order_no"]] = {
                    "name": row.get("name", "No Name"),
                    "code": row["order_no"],
                    "steps": [row_case],
                }
            else:
                orders_data[row["order_no"]]["steps"].append(row)
        return orders_data

    def import_order(self, order=False):
        if order:
            for step in order.get("steps", []):
                self.run_import_step(step)
        else:
            pass

    def run_import_step(self, step):
        if self.log_checks:
            _logger.info(
                "Running test step: %s - %s - %s",
                step.get("order_no"),
                step.get("name"),
                step.get("type"),
            )
        if step.get("type") == "sale":
            self.create_sale_order(step)
        elif step.get("type") == "purchase":
            self.create_purchase(step)
        elif step.get("type") == "inventory":
            self.create_stock_inventory(step)
        elif step.get("type") == "transfer_transit":
            self.create_internal_transfer_transit(step)
        elif step.get("type") == "transfer_direct":
            self.create_internal_transfer_direct(step)
        elif step.get("type") == "consume":
            self.create_stock_picking("consume", step)
        elif step.get("type") == "consume_production":
            self.create_stock_picking("production", step)
        elif step.get("type") == "usage_giving":
            self.create_stock_picking("usage_giving", step)
        elif step.get("type") == "dropship":
            self.create_sale_dropship(step)

    def get_references_from_values(self, values):
        refs = [
            "partner_id",
            "fiscal_position_id",
            "product_id",
            "currency_id",
            "location",
            "location1",
            "lot1",
            "lot2",
        ]
        float_keys = [
            "step",
            "qty",
            "stock_qty",
            "inv_qty",
            "stock_qty2",
            "inv_qty2",
            "price",
            "inv_price",
            "inv_price2",
            "discount",
            "advance",
            "landed_cost",
        ]
        bool_keys = ["notice", "reception_in_progress"]
        try:
            for key in values.keys():
                if key in refs and values.get(key, False):
                    value = values[key]
                    if "." not in value:
                        value = "l10n_ro_demo_data.%s" % value
                    if self.env.ref(value, raise_if_not_found=False):
                        values[key] = self.env.ref(value)
                if key in float_keys and values.get(key, False):
                    values[key] = float(values[key])
                if key in bool_keys and values.get(key, False):
                    values[key] = bool(float(values[key]))
        except Exception as e:
            _logger.debug("Error getting references from values: %(error)s", error=e)
            pass
        return dict(values)

    def get_stock_quantity(self, values, step):
        if step == 1:
            return values.get("stock_qty", 1)
        elif step == 2:
            return values.get("stock_qty2", 1)
        else:
            return 1

    def get_stock_lot(self, values, step):
        if step == 1:
            return values.get("lot1")  # None dacă nu există
        elif step == 2:
            return values.get("lot2")  # None dacă nu există
        return None

    def get_invoice_quantity(self, values, step):
        if step == 1:
            return values.get("inv_qty")  # None dacă nu există
        elif step == 2:
            return values.get("inv_qty2")  # None dacă nu există
        return None

    def get_invoice_price(self, values, step):
        price = values.get("price", 0)
        if step == 1:
            price = values.get("inv_price")  # None dacă nu există
        elif step == 2:
            price = values.get("inv_price2")  # None dacă nu există
        return price

    def create_sale_order(self, values):
        so_values = self.get_references_from_values(values)
        order_line = [
            (
                0,
                0,
                {
                    "product_id": so_values["product_id"].id,
                    "product_uom_qty": so_values.get("qty", 1),
                    "price_unit": so_values.get("price", 100),
                    "discount": so_values.get("discount", 0),
                },
            )
        ]
        fpos = False
        if so_values.get("fiscal_position_id", False):
            fpos = so_values["fiscal_position_id"].id
        vals = {
            "partner_id": so_values["partner_id"].id,
            "partner_invoice_id": so_values["partner_id"].id,
            "fiscal_position_id": fpos,
            "partner_shipping_id": so_values["partner_id"].id,
            "currency_id": so_values.get(
                "currency_id", self.env.company.currency_id
            ).id,
            "order_line": order_line,
            "client_order_ref": so_values.get("ref", False),
        }
        if so_values.get("location", False):
            warehouse = so_values["location"].warehouse_id
            if warehouse:
                vals["warehouse_id"] = warehouse.id
        sale = self.env["sale.order"].create(vals)
        sale.action_confirm()
        if so_values.get("advance") != 0:
            product = self.advance_product
            if product:
                adv_wiz = (
                    self.env["sale.advance.payment.inv"]
                    .with_context(active_ids=[sale.id])
                    .create(
                        {
                            "advance_payment_method": "percentage",
                            "amount": 50.0,
                            "product_id": product.id,
                        }
                    )
                )
                act = adv_wiz.with_context(open_invoices=True).create_invoices()
                invoice = self.env["account.move"].browse(act["res_id"])
                invoice.action_post()
        self.deliver_and_invoice_sales(sale, so_values)
        if values.get("step") == 2:
            self.deliver_and_invoice_sales(sale.with_context(step=2), so_values)
        return sale

    def deliver_and_invoice_sales(self, sales, values):
        for sale in sales:
            step = sale.env.context.get("step", 1)
            stock_qty = self.get_stock_quantity(values, step)
            invoice_qty = self.get_invoice_quantity(values, step)
            invoice_price = self.get_invoice_price(values, step)
            stock_lot = self.get_stock_lot(values, step)
            picking = self.env["stock.picking"]
            if step == 2 and stock_qty < 0:
                stock_qty = -stock_qty
                # Create return to initial reception
                picking = sale.picking_ids.filtered(lambda x: x.state == "done")
                if picking:
                    stock_return_picking_form = Form(
                        self.env["stock.return.picking"].with_context(
                            active_ids=picking.ids,
                            active_id=picking.ids[0],
                            active_model="stock.picking",
                        )
                    )
                    return_wiz = stock_return_picking_form.save()
                    return_wiz.product_return_moves.write(
                        {
                            "quantity": stock_qty,
                            "to_refund": True,
                        }
                    )
                    if stock_lot:
                        lot = getattr(self, stock_lot)
                        return_wiz.product_return_moves.write({"lot_id": lot.id})
                    res = return_wiz.action_create_returns()
                    return_pick = self.env["stock.picking"].browse(res["res_id"])
                    if values.get("notice"):
                        return_pick.l10n_ro_notice = values.get("notice")
                    return_pick.action_confirm()
                    return_pick.action_assign()
                    return_pick.move_ids._set_quantity_done(stock_qty)
                    return_pick.move_ids.picked = True
                    return_pick._action_done()
                    picking = return_pick
            else:
                # Create reception
                pickings = sale.picking_ids.filtered(lambda x: x.state != "done")
                if pickings:
                    picking = pickings[0]
                    picking.write(
                        {
                            "l10n_ro_notice": values.get("notice"),
                            "scheduled_date": sale.date_order,
                            "date_done": sale.date_order,
                        }
                    )
                    picking.move_ids._set_quantity_done(stock_qty)
                    if stock_lot:
                        lot = getattr(self, stock_lot)
                        picking.move_ids.write({"lot_id": lot.id})
                    picking.move_ids.picked = True
                    picking.button_validate()
                    if picking.state == "assigned":
                        picking._action_done()
            if picking.state == "done" and invoice_qty:
                invoice = self.env["account.move"]
                try:
                    invoices = sale._create_invoices(final=True)
                    invoice = invoices[0]
                except Exception as e:
                    _logger.info("Error creating invoice: %(error)s", error=e)
                if invoice:
                    invoice_line = invoice.invoice_line_ids[0]
                    if (
                        invoice_qty
                        and invoice_qty < 0
                        and invoice.move_type == "out_refund"
                    ):
                        invoice_qty = -invoice_qty
                    invoice_line.write(
                        {"quantity": invoice_qty, "price_unit": invoice_price}
                    )
                    invoice.write(
                        {
                            "date": sale.date_order,
                            "invoice_date": sale.date_order,
                            "invoice_date_due": sale.date_order,
                        }
                    )
                    invoice.action_post()

    def create_purchase(self, values):
        po_values = self.get_references_from_values(values)
        order_line = [
            (
                0,
                0,
                {
                    "product_id": po_values["product_id"].id,
                    "product_qty": po_values.get("qty", 1),
                    "price_unit": po_values.get("price", 80),
                },
            )
        ]
        fpos = False
        if po_values.get("fiscal_position_id", False):
            fpos = po_values["fiscal_position_id"].id
        vals = {
            "partner_id": po_values["partner_id"].id,
            "currency_id": po_values.get(
                "currency_id", self.env.company.currency_id
            ).id,
            "fiscal_position_id": fpos,
            "order_line": order_line,
            "origin": po_values.get("ref", False),
        }

        if po_values.get("location", False):
            picking_type = self.env["stock.picking.type"].search(
                [
                    ("company_id", "=", self.env.company.id),
                    ("default_location_src_id.usage", "=", "supplier"),
                    ("default_location_dest_id", "=", po_values["location"].id),
                ],
                limit=1,
                order="sequence",
            )
            if picking_type:
                vals["picking_type_id"] = picking_type.id

        purchase = self.env["purchase.order"].create(vals)
        purchase.onchange_partner_id()
        purchase.button_confirm()
        if values.get("reception_in_progress"):
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
        self.receive_and_invoice_purchases(purchase, po_values)
        if values.get("step") == 2:
            self.receive_and_invoice_purchases(purchase.with_context(step=2), po_values)
        return purchase

    def receive_and_invoice_purchases(self, purchases, values):
        for purchase in purchases:
            step = purchase.env.context.get("step", 1)
            stock_qty = self.get_stock_quantity(values, step)
            invoice_qty = self.get_invoice_quantity(values, step)
            invoice_price = self.get_invoice_price(values, step)
            stock_lot = self.get_stock_lot(values, step)
            picking = self.env["stock.picking"]
            invoice = self.env["account.move"]
            if step == 2 and stock_qty < 0:
                # Create return to initial reception
                stock_qty = -stock_qty
                picking = purchase.picking_ids.filtered(lambda x: x.state == "done")
                if picking:
                    stock_return_picking_form = Form(
                        self.env["stock.return.picking"].with_context(
                            active_ids=picking.ids,
                            active_id=picking.ids[0],
                            active_model="stock.picking",
                        )
                    )
                    return_wiz = stock_return_picking_form.save()
                    return_wiz.product_return_moves.write(
                        {
                            "quantity": stock_qty,
                            "to_refund": True,
                        }
                    )
                    if stock_lot:
                        lot = getattr(self, stock_lot)
                        return_wiz.product_return_moves.write({"lot_id": lot.id})
                    res = return_wiz.action_create_returns()
                    return_pick = self.env["stock.picking"].browse(res["res_id"])
                    return_pick.action_confirm()
                    return_pick.action_assign()
                    return_pick.move_ids._set_quantity_done(stock_qty)
                    return_pick.move_ids.picked = True
                    return_pick._action_done()
                    picking = return_pick
            else:
                # Create reception
                pickings = purchase.picking_ids.filtered(lambda x: x.state != "done")
                if pickings:
                    picking = pickings[0]
                    picking.write(
                        {
                            "l10n_ro_notice": values.get("notice"),
                            "scheduled_date": purchase.date_planned,
                            "date_done": purchase.date_planned,
                        }
                    )
                    picking.move_ids._set_quantity_done(stock_qty)
                    if stock_lot:
                        lot = getattr(self, stock_lot)
                        picking.move_ids.write({"lot_id": lot.id})
                    picking.move_ids.picked = True
                    picking.button_validate()
                    if picking.state == "assigned":
                        picking._action_done()
            if picking.state == "done" and invoice_qty:
                try:
                    action = purchase.action_create_invoice()
                    invoice = self.env["account.move"].browse(action["res_id"])
                except Exception as e:
                    _logger.info("Error creating invoice: %(error)s", error=e)
                if invoice:
                    invoice_line = invoice.invoice_line_ids[0]
                    if (
                        invoice_qty
                        and invoice_qty < 0
                        and invoice.move_type == "in_refund"
                    ):
                        invoice_qty = -invoice_qty
                    invoice_line.write(
                        {"quantity": invoice_qty, "price_unit": invoice_price}
                    )
                    invoice.write(
                        {
                            "date": purchase.date_planned,
                            "invoice_date": purchase.date_planned,
                            "invoice_date_due": purchase.date_planned,
                        }
                    )
                    invoice.with_context(
                        l10n_ro_approved_price_difference=True
                    ).action_post()
            if picking.state == "done":
                if values.get("landed_cost", 0) != 0:
                    self.create_landed_cost(invoice, picking, values)

    def create_stock_inventory(self, values):
        inventory_values = self.get_references_from_values(values)
        inventory_vals = {
            "product_id": inventory_values["product_id"].id,
            "location_id": inventory_values["location"].id,
            "inventory_quantity": inventory_values.get("stock_qty", 0),
        }
        if inventory_values.get("lot1"):
            lot = inventory_values["lot1"]
            inventory_vals["lot_id"] = lot.id
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            inventory_vals
        ).action_apply_inventory()

    def create_internal_transfer_transit(self, values, picking=None):
        transfer_values = self.get_references_from_values(values)
        step = 1
        if picking:
            step = picking.env.context.get("step", 1)

        stock_qty = self.get_stock_quantity(values, step)
        stock_lot = self.get_stock_lot(values, step)
        if step == 2 and stock_qty < 0:
            # Create return to initial transfer
            stock_qty = -stock_qty
            stock_return_picking_form = Form(
                self.env["stock.return.picking"].with_context(
                    active_ids=[picking.id],
                    active_id=picking.id,
                    active_model="stock.picking",
                )
            )
            return_wiz = stock_return_picking_form.save()
            return_wiz.product_return_moves.write(
                {
                    "quantity": stock_qty,
                    "to_refund": True,
                }
            )
            if stock_lot:
                lot = getattr(self, stock_lot)
                return_wiz.product_return_moves.write({"lot_id": lot.id})
            res = return_wiz.action_create_returns()
            return_pick = self.env["stock.picking"].browse(res["res_id"])
            return_pick.action_confirm()
            return_pick.action_assign()
            return_pick.move_ids._set_quantity_done(stock_qty)
            return_pick.move_ids.picked = True
            return_pick._action_done()
            return return_pick
        step = 1
        if picking:
            step = picking.env.context.get("step", 1)
        move_vals = {
            "company_id": self.env.company.id,
            "location_id": transfer_values.get("location").id,
            "location_dest_id": self.transit_loc.id,
            "product_id": transfer_values.get("product_id").id,
            "product_uom": transfer_values.get("product_id").uom_id.id,
            "product_uom_qty": transfer_values.get("qty", 1),
            "route_ids": [(4, self.transit_route.id)],
        }
        if stock_lot:
            lot = getattr(self, stock_lot)
            move_vals["lot_ids"] = [(6, 0, [lot.id])]
        move_transit_out = self.env["stock.move"].create(move_vals)
        move_transit_out._action_confirm()
        move_transit_out._action_assign()
        move_transit_out._set_quantity_done(stock_qty)
        move_transit_out.picked = True
        move_transit_out._action_done()
        move_transit_in = move_transit_out.move_dest_ids
        self.assertTrue(move_transit_in, "No move created from push rules")
        self.assertEqual(move_transit_in.state, "assigned")
        picking_receipt = move_transit_in.picking_id
        picking_receipt.move_ids.picked = True
        picking_receipt.button_validate()
        if values.get("step") == 2:
            self.create_internal_transfer_transit(
                values, picking_receipt.with_context(step=2)
            )
        return picking_receipt

    def create_internal_transfer_direct(self, values, picking=None):
        transfer_values = self.get_references_from_values(values)
        step = 1
        if picking:
            step = picking.env.context.get("step", 1)
        stock_qty = self.get_stock_quantity(values, step)
        stock_lot = self.get_stock_lot(values, step)
        if step == 2 and stock_qty < 0:
            # Create return to initial transfer
            stock_qty = -stock_qty
            stock_return_picking_form = Form(
                self.env["stock.return.picking"].with_context(
                    active_ids=[picking.id],
                    active_id=picking.id,
                    active_model="stock.picking",
                )
            )
            return_wiz = stock_return_picking_form.save()
            return_wiz.product_return_moves.write(
                {
                    "quantity": stock_qty,
                    "to_refund": True,
                }
            )
            if stock_lot:
                lot = getattr(self, stock_lot)
                return_wiz.product_return_moves.write({"lot_id": lot.id})
            res = return_wiz.action_create_returns()
            return_pick = self.env["stock.picking"].browse(res["res_id"])
            return_pick.action_confirm()
            return_pick.action_assign()
            return_pick.move_ids._set_quantity_done(stock_qty)
            return_pick.move_ids.picked = True
            return_pick._action_done()
            return return_pick
        move_vals = {
            "company_id": self.env.company.id,
            "location_id": transfer_values.get("location").id,
            "location_dest_id": transfer_values.get("location1").id,
            "product_id": transfer_values.get("product_id").id,
            "product_uom": transfer_values.get("product_id").uom_id.id,
            "product_uom_qty": stock_qty,
        }
        if stock_lot:
            lot = getattr(self, stock_lot)
            move_vals["lot_ids"] = [(6, 0, [lot.id])]
        move_transfer = self.env["stock.move"].create(move_vals)
        move_transfer._action_confirm()
        move_transfer._action_assign()
        move_transfer._set_quantity_done(stock_qty)
        move_transfer.picked = True
        move_transfer._action_done()
        picking_receipt = move_transfer.picking_id
        if values.get("step") == 2:
            self.create_internal_transfer_direct(
                values, picking_receipt.with_context(step=2)
            )
        return picking_receipt

    def create_stock_picking(self, oper_type, values, picking=None):
        picking_values = self.get_references_from_values(values)
        step = 1
        if picking:
            step = picking.env.context.get("step", 1)
        stock_qty = self.get_stock_quantity(values, step)
        stock_lot = self.get_stock_lot(values, step)
        if step == 2 and stock_qty < 0:
            # Create return to initial operation
            stock_qty = -stock_qty
            stock_return_picking_form = Form(
                self.env["stock.return.picking"].with_context(
                    active_ids=[picking.id],
                    active_id=picking.id,
                    active_model="stock.picking",
                )
            )
            return_wiz = stock_return_picking_form.save()
            return_wiz.product_return_moves.write(
                {
                    "quantity": stock_qty,
                    "to_refund": True,
                }
            )
            if stock_lot:
                lot = getattr(self, stock_lot)
                return_wiz.product_return_moves.write({"lot_id": lot.id})
            res = return_wiz.action_create_returns()
            return_pick = self.env["stock.picking"].browse(res["res_id"])
            return_pick.action_confirm()
            return_pick.action_assign()
            return_pick.move_ids._set_quantity_done(stock_qty)
            return_pick.move_ids.picked = True
            return_pick._action_done()
            return return_pick
        if not picking_values.get("location"):
            _logger.warning(
                "You need to provide the location source for stock operations"
            )
            pass
        domain = [
            ("company_id", "=", self.env.company.id),
            ("default_location_src_id", "=", picking_values["location"].id),
            ("default_location_dest_id.usage", "=", oper_type),
        ]
        if picking_values.get("location1"):
            domain.append(
                ("default_location_dest_id", "=", picking_values["location1"].id)
            )
        picking_type = self.env["stock.picking.type"].search(domain)
        if not picking_type:
            _logger.warning(
                self.env._(
                    "No picking type found for type %(picking_type)s and locations %(location)s %(location1)s.",  # noqa
                    picking_type=oper_type,
                    location=picking_values.get("location"),
                    location1=picking_values.get("location1"),
                )
            )
        picking_type.use_existing_lots = True
        location_src = picking_type.default_location_src_id.id
        location_dest = picking_type.default_location_dest_id.id
        product = picking_values.get("product_id")
        picking_vals = {
            "location_id": location_src,
            "location_dest_id": location_dest,
            "picking_type_id": picking_type.id,
        }
        if picking_values.get("partner_id"):
            picking_vals["partner_id"] = picking_values["partner_id"].id
        picking = self.env["stock.picking"].create(picking_vals)
        move_vals = {
            "location_id": location_src,
            "location_dest_id": location_dest,
            "picking_id": picking.id,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": picking_values.get("qty", 1),
        }
        if stock_lot:
            lot = getattr(self, stock_lot)
            move_vals["lot_ids"] = [(6, 0, [lot.id])]
        move = self.env["stock.move"].create(move_vals)
        picking.action_confirm()
        picking.action_assign()
        move._set_quantity_done(stock_qty)

        picking.button_validate()
        if step == 1 and picking_values.get("step") == 2:
            self.create_stock_picking(oper_type, values, picking.with_context(step=2))
        return picking

    def create_landed_cost(self, invoice, picking, values):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "general")],
            limit=1,
        )
        product = self.landed_cost
        landed_cost = self.env["stock.landed.cost"].create(
            {
                "picking_ids": [(4, picking.id)],
                "vendor_bill_id": invoice.id if invoice else False,
                "account_journal_id": journal.id,
                "date": invoice.date if invoice else picking.scheduled_date,
                "cost_lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "price_unit": values.get("landed_cost"),
                            "split_method": "equal",
                            "account_id": product.property_account_expense_id.id,
                        },
                    )
                ],
            }
        )
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()
