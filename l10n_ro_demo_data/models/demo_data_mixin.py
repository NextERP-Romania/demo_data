# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

import logging
import random
import csv
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


class RomaniaTestDataMixin(models.Model):
    _name = "nexterp.demodata.mixin"
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
            "l10n_ro_vat_subjected": l10n_ro_vat_subjected,
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
            else "real_time",
            "property_stock_valuation_account_id": stock_acc.id,
            # "property_stock_account_input_categ_id": stock_acc.id,
            # "property_stock_account_output_categ_id": stock_acc.id,
            "property_account_income_categ_id": income_acc.id,
            "property_account_expense_categ_id": expense_acc.id,
        }
        vals.update(values)
        return self.env["product.category"].create(vals)

    def update_test_record_product_category(self, category, prod_type="product"):
        acc_obj = self.env["account.account"]
        categ_mapping = [
            ("marfuri", "371000", "607000", "707000"),
            ("materii_prime", "301000", "601000", "702000"),
            ("produse_finite", "345000", "711000", "701500"),
            ("ambalaje", "308000", "608000", "707000"),
            ("combustibil", "302200", "602200", "707000"),
            ("consumabile", "302800", "602800", "702000"),
            ("service", "371000", "628000", "704000"),
        ]
        vals = {
            "property_cost_method": "fifo" if prod_type != "service" else "standard",
            "property_valuation": "real_time"
            if prod_type != "service"
            else "real_time",
        }
        line_categ = False
        for line in categ_mapping:
            if line[0] == prod_type:
                line_categ = line
        if line_categ:
            stock_acc = acc_obj.search([("code", "=", line_categ[1])])
            expense_acc = acc_obj.search([("code", "=", line_categ[2])])
            income_acc = acc_obj.search([("code", "=", line_categ[3])])
            vals.update(
                {
                    "property_stock_valuation_account_id": stock_acc.id,
                    # "property_stock_account_input_categ_id": stock_acc.id,
                    # "property_stock_account_output_categ_id": stock_acc.id,
                    "property_account_income_categ_id": income_acc.id,
                    "property_account_expense_categ_id": expense_acc.id,
                }
            )
        category.write(vals)
        return category

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
                ("description", "=", "TVA colectat 19% Servicii"),
                ("company_id", "=", self.env.company.id),
            ]
        )
        purch_serv_tax = self.env["account.tax"].search(
            [
                ("description", "=", "TVA deductibil 19% Servicii"),
                ("company_id", "=", self.env.company.id),
            ]
        )

        product_category = self._get_random_product_category(exp_acc)
        list_price = fake_data.pyfloat(right_digits=2, min_value=100, max_value=25000)
        vals = {
            "name": name,
            "type": prod_type,
            "is_storable": True if prod_type != "service" else False,
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

    def get_record_ref(self, ref):
        module = "l10n_ro_demo_data."
        record = ref
        if "." in ref:
            module = ref.split(".")[0] + "."
            record = ref.split(".")[1]
        return self.env.ref(module + record, raise_if_not_found=False)

    def get_references_from_values(self, values):
        refs = ["partner_id", "fiscal_position_id", "product_id", "currency_id"]
        for key in values:
            if key in refs:
                values[key] = self.get_record_ref(values[key])
        return dict(values)

    def clean_values(self, values):
        clean_values = ["qty", "inv_qty", "price", "discount", "advance", "notice", "price_diff", "landed_cost", "reception_in_progress"]
        for key in clean_values:
            if key in values:
                values.pop(key)
        return values