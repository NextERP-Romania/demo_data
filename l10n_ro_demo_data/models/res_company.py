# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_account(self, code):
        domain = [("code", "=", code), ("company_id", "=", self.id)]
        account = self.env["account.account"].search(domain, limit=1)
        return account.id if account else False

    def install_demo_data(self):
        self.ensure_one()
        self.update_company_config()
        self.env["nexterp.demodata"].install_demo_data(company=self)

    def update_company_config(self):
        self.ensure_one()
        acc_obj = self.env["account.account"]
        afp_obj = self.env["account.fiscal.position"]
        for company in self:
            self.env['ir.config_parameter'].set_param('sale.automatic_invoice', "delivery")
            avans_products = self.env["product.product"].search([]).filtered(
                lambda p: "Avans" in p._name
            )
            avans_products.write(
                {
                    "property_account_income_id": self.get_account("419000"),
                    "property_account_expense_id": self.get_account("409000"),
                }
            )
            avans_prod = self.env.ref(
                "l10n_ro_demo_data.nexterp_demo_product_19", raise_if_not_found=False
            )
            self.env["ir.config_parameter"].sudo().set_param(
                "sale.default_deposit_product_id", avans_prod.id
            )
            inv_text = (
                "Factura circulă fără semnătură și ștampilă conform legii "
                "227/2015, regula 319, paragraful 29."
            )
            # Add services taxes to configuration
            sale_serv_tax = self.env["account.tax"].search(
                [
                    ("name", "=", "TVA colectat 19% Servicii"),
                    ("company_id", "=", company.id),
                ]
            )
            purch_serv_tax = self.env["account.tax"].search(
                [
                    ("name", "=", "TVA deductibil 19% Servicii"),
                    ("company_id", "=", company.id),
                ]
            )
            _logger.info("Update and configure company %s data." % (company.name))
            company.partner_id.vat = "RO39187746"
            company.partner_id.ro_vat_change()
            company.write(
                {
                    # "caen_code": "6202",
                    "anglo_saxon_accounting": True,
                    "l10n_ro_accounting": True,
                    "l10n_ro_stock_acc_price_diff": True,
                    "company_registry": "J35/1254/2018",
                    "phone": "0770816455",
                    "email": "contact@nexterp.ro",
                    "website": "https://nexterp.ro",
                    "l10n_ro_account_serv_sale_tax_id": sale_serv_tax,
                    "l10n_ro_account_serv_purchase_tax_id": purch_serv_tax,
                    "l10n_ro_property_stock_picking_payable_account_id": self.get_account("408000"),
                    "l10n_ro_property_stock_picking_receivable_account_id": self.get_account("418000"),
                    "l10n_ro_property_stock_usage_giving_account_id": self.get_account("803500"),
                    "l10n_ro_property_stock_picking_custody_account_id": self.get_account("803300"),
                    "l10n_ro_property_uneligible_tax_account_id": self.get_account("442820"),
                    "l10n_ro_property_trade_discount_received_account_id": self.get_account("609000"),
                    "l10n_ro_property_trade_discount_granted_account_id": self.get_account("709000"),
                    "l10n_ro_property_vat_on_payment_position_id": afp_obj.search(
                        [
                            ("name", "=", "Regim TVA la Incasare"),
                            ("company_id", "=", company.id),
                        ]
                    ),
                    "l10n_ro_property_inverse_taxation_position_id": afp_obj.search(
                        [
                            ("name", "=", "Regim Taxare Inversa"),
                            ("company_id", "=", company.id),
                        ]
                    ),
                    "l10n_ro_no_signature_text": inv_text,
                }
            )

        rcs_model = self.env["res.config.settings"]
        acs_ids = rcs_model.search([("company_id", "=", company.id)])
        values = {
            "group_multi_currency": True,
            "group_show_sale_receipts": True,
            "group_show_purchase_receipts": True,
            "group_sale_delivery_address": True,
            "group_proforma_sales": True,
            "group_stock_multi_locations": True,
            "module_sale_margin": True,
            "extract_single_line_per_tax": False,
            "module_account_invoice_extract": False,
            "module_snailmail_account": False,
            "module_partner_autocomplete": False,
            "module_stock_sms": False,
        }
        if acs_ids:
            acs_ids.write(values)
