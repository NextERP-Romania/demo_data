# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

import logging
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import faker
    import faker_commerce
except (ImportError, IOError) as err:
    _logger.debug(err)


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


def random_numbers(length):
    return "".join(["%s" % random.randint(0, 9) for num in range(0, length)])


EMAIL_DOMAIN = "@odooerpromania.ro"
PASSWORD = "odooerpromania"


class RomaniaTestData(models.Model):
    _name = "nexterp.demodata"
    _description = "Configure company and create demo data"

    def _get_random_customer(self):
        return random.choice(
            self.env["res.partner"].search(
                [("customer_rank", ">", 0), ("is_company", "=", True)]
            )
        )

    def _get_random_supplier(self):
        return random.choice(
            self.env["res.partner"].search(
                [("supplier_rank", ">", 0), ("is_company", "=", True)]
            )
        )

    def _get_random_product_category(self, exp_acc="607000"):
        return random.choice(
            self.env["product.category"].search(
                [("property_account_expense_categ_id.code", "=", exp_acc)]
            )
        )

    def _get_random_product(self, prod_type="product"):
        return random.choice(
            self.env["product.product"].search([("type", "=", prod_type)])
        )

    def _pay_invoice(self, invoice):
        journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("at_least_one_inbound", "=", True)], limit=1
        )
        values = (
            self.env["account.payment"]
            .with_context(default_invoice_ids=[(6, 0, [invoice.id])])
            .default_get(["invoice_ids"])
        )
        values.update(
            {
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "journal_id": journal.id,
            }
        )
        payment = self.env["account.payment"].create(values)
        payment.action_validate_invoice_payment()

    @api.model
    def create_test_record(self, model, values):
        """Create new odoo record."""
        if not model:
            return False
        model_obj = self.env[model]
        if not values:
            values = model_obj.default_get(list(model_obj._fields.keys()))
        return model_obj.create(values)

    @api.model
    def create_test_record_res_partner(self, country_code):
        """Create new partner."""
        values = self._context.get("values", {})
        language = "{}_{}".format(country_code.lower(), country_code.upper())
        fake_data = faker.Faker(language)
        state = False
        country = self.env["res.country"].search([("code", "=", country_code)])
        if country:
            country = country[0].id
            states = self.env["res.country.state"].search(
                [("country_id", "=", country)]
            )
            if states:
                state = random.choice(states).id
        l10n_ro_vat_subjected = random.choice([True, False])
        vals = {
            "name": fake_data.company(),
            "email": fake_data.email(),
            "is_company": True,
            "street": fake_data.street_address(),
            "zip": fake_data.postcode(),
            "city": fake_data.city(),
            "state_id": state,
            "country_id": country,
            "phone": fake_data.phone_number(),
            "l10n_ro_l10n_ro_vat_subjected": l10n_ro_vat_subjected,
            "customer_rank": int(fake_data.boolean()),
            "supplier_rank": int(fake_data.boolean()),
        }
        vals.update(values)

        partner = self.create_test_record("res.partner", vals)
        vat_generated = False
        while not vat_generated:
            vat_number = False
            if hasattr(fake_data, "vat_id"):
                vat_number = fake_data.vat_id()
            elif hasattr(fake_data, "businesses_inn"):
                vat_number = fake_data.businesses_inn()
            elif hasattr(fake_data, "ssn"):
                vat_number = fake_data.ssn()
            if vat_number:
                try:
                    partner.write({"vat": vat_number})
                    vat_generated = True
                except ValidationError:
                    pass

        return partner

    @api.model
    def partners_generate_vat(self):
        partners = self.env["res.partner"].search([("is_company", "=", True)])
        for partner in partners:
            country_code = partner.country_id.code
            if country_code:
                language = "{}_{}".format(country_code.lower(), country_code.upper())
                fake_data = faker.Faker(language)
            else:
                fake_data = faker.Faker()
            vat_generated = False
            while not vat_generated:
                vat_number = fake_data.vat_id()
                try:
                    partner.write({"vat": vat_number})
                    vat_generated = True
                except ValidationError:
                    pass

    @api.model
    def create_test_record_partner_contact(self, partner, contact_type, country_code):
        """Create new partner contact.
        :param: int partner_id: id for partner to this address
        """
        values = self._context.get("values", {})
        language = "{}_{}".format(country_code.lower(), country_code.upper())
        fake_data = faker.Faker(language)
        state = False
        country = self.env["res.country"].search([("code", "=", country_code)])
        if country:
            country = country[0].id
            states = self.env["res.country.state"].search(
                [("country_id", "=", country)]
            )
            if states:
                state = random.choice(states).id
        vals = {
            "name": fake_data.name(),
            "email": fake_data.email(),
            "parent_id": partner.id if partner else False,
            "country_id": self.env.ref("base.ro").id,
            "zip": fake_data.postcode(),
            "street": fake_data.street_address(),
            "city": fake_data.city(),
            "state_id": state,
            "type": contact_type,
        }
        vals.update(values)

        return self.create_test_record("res.partner", vals)

    @api.model
    def create_test_record_res_users(self, country_code):
        """Create new user."""
        values = self._context.get("values", {})
        language = "{}_{}".format(country_code.lower(), country_code.upper())
        fake_data = faker.Faker(language)
        if not values.get("name"):
            values["name"] = fake_data.name()
        if not values.get("email"):
            values["email"] = fake_data.email()

        if not values.get("login") and values.get("email"):
            values["login"] = values["email"]

        groups_id = []
        if values.get("groups_id", ""):
            for group_ref in values.get("groups_id", "").split(","):
                group = self.env.ref(group_ref)
                if group:
                    groups_id.append(group.id)
        if groups_id:
            values["groups_id"] = [(6, 0, groups_id)]
        return self.create_test_record("res.users", values)

    def create_test_record_product_category(self, name, prod_type="product"):
        acc_obj = self.env["account.account"]
        values = self._context.get("values", {})
        parent = self._get_random_product_category()
        if prod_type == "product":
            stock_acc = acc_obj.search([("code", "=", "371000")])
            expense_acc = acc_obj.search([("code", "=", "607000")])
            income_acc = acc_obj.search([("code", "=", "707000")])
        elif prod_type == "consumable":
            stock_acc = acc_obj.search([("code", "=", "302800")])
            expense_acc = acc_obj.search([("code", "=", "602800")])
            income_acc = acc_obj.search([("code", "=", "702000")])
        elif prod_type == "service":
            stock_acc = acc_obj.search([("code", "=", "371000")])
            expense_acc = acc_obj.search([("code", "=", "628000")])
            income_acc = acc_obj.search([("code", "=", "704000")])
        vals = {
            "name": name,
            "parent_id": parent.id,
            "property_cost_method": "fifo" if prod_type != "service" else "standard",
            "property_valuation": "real_time"
            if prod_type != "service"
            else "manual_periodic",
            "property_stock_valuation_account_id": stock_acc.id,
            "property_stock_account_input_categ_id": stock_acc.id,
            "property_stock_account_output_categ_id": stock_acc.id,
            "property_account_income_categ_id": income_acc.id,
            "property_account_expense_categ_id": expense_acc.id,
        }
        vals.update(values)
        return self.env["product.category"].create(vals)

    def create_test_record_product(self, country_code, prod_type="product"):
        values = self._context.get("values", {})
        language = "{}_{}".format(country_code.lower(), country_code.upper())
        fake_data = faker.Faker(language)
        fake_data.add_provider(faker_commerce.Provider)
        name = fake_data.ecommerce_name()
        exp_acc = "607000"
        if prod_type == "consumable":
            exp_acc = "602800"
        elif prod_type == "service":
            exp_acc = "628000"
        if prod_type == "consumable":
            prod_type = "product"
        sale_serv_tax = self.env["account.tax"].search(
            [
                ("name", "=", "TVA colectat 19% Servicii"),
                ("company_id", "=", self.env.company.id),
            ]
        )
        purch_serv_tax = self.env["account.tax"].search(
            [
                ("name", "=", "TVA deductibil 19% Servicii"),
                ("company_id", "=", self.env.company.id),
            ]
        )

        product_category = self._get_random_product_category(exp_acc)
        list_price = fake_data.pyfloat(right_digits=2, min_value=100, max_value=25000)
        vals = {
            "name": name,
            "type": prod_type,
            "categ_id": product_category.id,
            "list_price": list_price,
        }
        if prod_type == "service":
            if sale_serv_tax:
                vals["taxes_id"] = sale_serv_tax
            if purch_serv_tax:
                vals["supplier_taxes_id"] = purch_serv_tax
        vals.update(values)
        return self.env["product.product"].create(vals)

    def products_add_supplier(self):
        products = self.env["product.product"].search([("type", "=", "product")])
        for product in products:
            supplier = self._get_random_supplier()
            product.write(
                {
                    "seller_ids": [
                        (
                            0,
                            0,
                            {
                                "partner_id": supplier.id,
                                "price": product.list_price
                                * random.choice([0.7, 0.75, 0.8, 0.65, 0.6]),
                            },
                        )
                    ],
                }
            )

    def create_test_record_sale_order(self):
        values = self._context.get("vals", {})
        partner = self._get_random_customer()
        prod_type = random.choice(["product", "service"])
        product = self._get_random_product(prod_type)
        country = partner.country_id
        fp = False
        sale_date = random.choice(days_last_month())
        vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "fiscal_position_id": fp,
            "partner_shipping_id": partner.id,
            "create_date": sale_date,
            "date_order": sale_date,
            "validity_date": sale_date,
            "commitment_date": sale_date,
            "effective_date": sale_date,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_qty": random.choice([1, 2, 3, 4, 5]),
                    },
                )
            ],
        }
        vals.update(values)
        sale = self.env["sale.order"].create(vals)
        sale.onchange_partner_id()
        sale.onchange_partner_shipping_id()
        if not sale.fiscal_position_id and country:
            eu_countries = self.env.ref("base.europe").country_ids
            if country != self.env.ref("base.ro"):
                if country in eu_countries:
                    fp_name = random.choice(
                        [
                            "Regim Intra-Comunitar (TVA)",
                            "Regim Intra-Comunitar Scutit",
                            "Regim Scutite - cu drept de deducere",
                            "Regim Scutite - fara drept de deducere",
                            "Regim Intra-Comunitar Neimpozabile",
                        ]
                    )
                else:
                    if country in eu_countries:
                        fp_name = "Regim Extra-Comunitar"
            else:
                fp_name = random.choice(
                    [
                        "Regim National (TVA)",
                        "Regim National",
                        "Regim Taxare Inversa",
                        "Regim TVA la Incasare",
                    ]
                )
            fp = self.env["account.fiscal.position"].search([("name", "=", fp_name)])
            if fp:
                sale.fiscal_position_id = fp[0]
        # To check why the dates are not updated
        return sale

    @api.model
    def confirm_purchases(self, purchases):
        for purchase in purchases:
            purdate = random.choice(days_last_month())
            purchase.write(
                {
                    "create_date": purdate,
                    "date_approve": purdate,
                    "date_planned": purdate,
                    "effective_date": purdate,
                }
            )
            purchase.onchange_partner_id()
            (
                country_code,
                identifier_type,
                vat_number,
            ) = purchase.partner_id.commercial_partner_id._parse_anaf_vat_info()
            sale = purchase.order_line.sale_order_id
            if identifier_type == "1":
                fp_name = random.choice(
                    [
                        "Regim National (TVA)",
                        "Regim National",
                        "Regim Taxare Inversa",
                        "Regim TVA la Incasare",
                    ]
                )
                if sale.fiscal_position_id.name in [
                    "Regim Taxare Inversa",
                    "Regim TVA la Incasare",
                ]:
                    fp_name = sale.fiscal_position_id.name
            elif identifier_type == "2":
                fp_name = "Regim National"
            elif identifier_type == "3":
                fp_name = random.choice(
                    [
                        "Regim Intra-Comunitar (TVA)",
                        "Regim Intra-Comunitar Scutit",
                        "Regim Scutite - cu drept de deducere",
                        "Regim Scutite - fara drept de deducere",
                        "Regim Intra-Comunitar Neimpozabile",
                    ]
                )
            else:
                fp_name = "Regim Extra-Comunitar"
            fp = self.env["account.fiscal.position"].search([("name", "=", fp_name)])
            if fp:
                purchase.fiscal_position_id = fp[0]
            fiz_person = (
                purchase.partner_id.country_id.id == self.env.ref("base.ro").id
                and not purchase.partner_id.l10n_ro_vat_subjected
            )
            if fp_name == "Regim National" or fiz_person:
                for line in purchase.order_line:
                    line.taxes_id = [(6, 0, [])]
            purchase.button_confirm()
            pickings = purchase.picking_ids
            if pickings:
                picking = pickings[0]
                picking.write(
                    {
                        "l10n_ro_notice": random.choice([True, False]),
                        "scheduled_date": purchase.date_planned,
                        "date_done": purchase.date_planned,
                    }
                )
                for ml in picking.move_line_ids:
                    ml.qty_done = ml.reserved_uom_qty
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
    def confirm_sales(self, sales):
        for sale in sales:
            pickings = sale.picking_ids
            if pickings:
                picking = pickings[0]
                picking.write(
                    {
                        "l10n_ro_notice": random.choice([True, False]),
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
                        ml.qty_done = ml.reserved_uom_qty
                    picking._action_done()
                if picking.state == "done":
                    invoices = sale._create_invoices()
                    invoices.write(
                        {
                            "invoice_date": sale.date_order,
                            "invoice_date_due": sale.date_order,
                        }
                    )
                    invoices.action_post()

    @api.model
    def create_partners(self, countries, number):
        for i in range(number):
            country = random.choice(countries)
            partner = self.create_test_record_res_partner(country)
            if i % 10 == 0:
                for c in range(3):
                    _logger.info("Create {} contact for {}".format(c, partner.name))
                    contact_type = random.choice(
                        ["contact", "invoice", "delivery", "other", "private"]
                    )
                    self.create_test_record_partner_contact(
                        partner, contact_type, country
                    )

    @api.model
    def install_demo_data(self, company):
        countries_eu = ["DE", "HU", "IT", "HR"]
        countries_exp = ["TR", "RU", "TH"]
        country_ro = "RO"
        acc_group = self.env.ref("account.group_account_user")
        users = self.env["res.users"].search([])
        for user in users:
            if acc_group and not user.has_group("account.group_account_user"):
                user.write({"groups_id": [(4, acc_group.id)]})
        partners = self.env["res.partner"].search([])
        if len(partners) < 50:
            self.create_partners(countries_eu, 100)
            self.create_partners(countries_exp, 50)
            self.create_partners(["RO"], 500)
        # Create 25 categories
        categories = self.env["product.category"].search([])
        if len(categories) < 25:
            language = "{}_{}".format(country_ro.lower(), country_ro.upper())
            fake_data = faker.Faker(language)
            fake_data.add_provider(faker_commerce.Provider)
            for i in range(25):
                categ_type = random.choice(["product", "consumable", "service"])
                name = fake_data.ecommerce_category()
                exist_categ = self.env["product.category"].search([("name", "=", name)])
                if exist_categ:
                    i -= 1
                else:
                    _logger.info("Create %s product category data." % i)
                    self.create_test_record_product_category(name, categ_type)
        # Create 200 products
        products = self.env["product.product"].search([])
        if len(products) < 200:
            for i in range(200):
                prod_type = random.choice(["product", "consumable"])
                _logger.info("Create %s product product data." % i)
                product = self.create_test_record_product(country_ro, prod_type)
                cust_tax_9 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 9% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                cust_tax_5 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 5% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                cust_tax_0 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 0% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_9 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 9% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_5 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 5% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_0 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 0% Bunuri"),
                        ("company_id", "=", company.id),
                    ]
                )
                if i % 10 == 0:
                    product.write(
                        {"taxes_id": cust_tax_9, "supplier_taxes_id": supp_tax_9}
                    )
                if i % 15 == 0:
                    product.write(
                        {"taxes_id": cust_tax_5, "supplier_taxes_id": supp_tax_5}
                    )
                if i % 19 == 0:
                    product.write(
                        {"taxes_id": cust_tax_0, "supplier_taxes_id": supp_tax_0}
                    )
                if i % 18 == 0:
                    d394_code = random.choice(self.env["anaf.product.code"].search([]))
                    product.write({"anaf_code_id": d394_code.id})
            # Create Services products
            for i in range(100):
                _logger.info("Create %s service product data." % i)
                product = self.create_test_record_product(country_ro, "service")
                product.type = "service"
                cust_tax_9 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 9% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                cust_tax_5 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 5% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                cust_tax_0 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA colectat 0% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_9 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 9% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_5 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 5% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                supp_tax_0 = self.env["account.tax"].search(
                    [
                        ("name", "=", "TVA deductibil 0% Servicii"),
                        ("company_id", "=", company.id),
                    ]
                )
                if i % 10 == 0:
                    product.write(
                        {"taxes_id": cust_tax_9, "supplier_taxes_id": supp_tax_9}
                    )
                if i % 15 == 0:
                    product.write(
                        {"taxes_id": cust_tax_5, "supplier_taxes_id": supp_tax_5}
                    )
                if i % 19 == 0:
                    product.write(
                        {"taxes_id": cust_tax_0, "supplier_taxes_id": supp_tax_0}
                    )
        # # Create 200 sale orders
        sales = self.env["sale.order"].search([], order="name asc")
        if len(sales) < 250:
            for i in range(250):
                _logger.info("Create %s sale order data." % i)
                self.create_test_record_sale_order()
        # Confirm 200 sale orders
        sales = self.env["sale.order"].search([("state", "=", "draft")])
        for sale in sales[:200]:
            _logger.info("Confirm %s sale order." % sale.name)
            sale.action_confirm()
        # self.products_add_supplier()
        # Run Scheduler to order Products
        self.env["stock.warehouse.orderpoint"].flush_model()
        self.env["stock.warehouse.orderpoint"]._get_orderpoint_action()
        self.env["stock.warehouse.orderpoint"].search([]).action_replenish_auto()
        # Confirm and Invoice Purchase Orders
        purchases = self.env["purchase.order"].search([("state", "=", "draft")])
        self.confirm_purchases(purchases)
        # Confirm and Invoice Sale Orders
        sales = self.env["sale.order"].search([("state", "=", "sale")])
        self.confirm_sales(sales)
