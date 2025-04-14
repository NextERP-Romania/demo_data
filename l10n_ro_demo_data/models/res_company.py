# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_account(self, code):
        domain = [("code", "=", code), ("company_ids", "in", [self.id])]
        account = self.env["account.account"].search(domain, limit=1)
        return account

    def install_demo_data(self):
        self.ensure_one()
        self.update_company_config()
        self.env["nexterp.demodata"].install_demo_data(company=self)
        self.env["nexterp.demodata"].create_demo_data_orders(company=self)

    def update_company_config(self):
        self.ensure_one()
        acc_obj = self.env["account.account"]
        afp_obj = self.env["account.fiscal.position"]
        self.env["product.product"].search([
            ("type", "=", "consu")
        ]).invoice_policy = "delivery"
        for company in self:
            company.country_id = self.env.ref("base.ro")
            company.partner_id.vat = "RO39187746"
            company.partner_id.ro_vat_change()
            journals = self.env["account.journal"].search([])
            if not journals:
                self.env['account.chart.template'].try_loading(
                    'ro',
                    company,
                    install_demo=False,
                    force_create=False,
                )
            self.env["nexterp.demodata"].configure_product_categories(company)
            self.env["nexterp.demodata"].configure_product_taxes(company)
            avans_products = self.env["product.product"].search([]).filtered(
                lambda p: "Avans" in p.name
            )
            avans_products.write(
                {
                    "property_account_income_id": self.get_account("419000").id,
                    "property_account_expense_id": self.get_account("409000").id,
                }
            )
            transport_products = self.env["product.product"].search([]).filtered(
                lambda p: "Transport" in p.name
            )
            
            transport_products.write(
                {
                    "property_account_income_id": self.get_account("707000").id,
                    "property_account_expense_id": self.get_account("624000").id,
                    "split_method_landed_cost": "equal",
                }
            )
            transport_products.product_tmpl_id.write({ "landed_cost_ok": True, })
            merchandise_acc = self.get_account("371000")
            # module_stock_account_reception_in_progress nu este updatat in 18.0
            # merchandise_acc.l10n_ro_reception_in_progress_account_id = self.get_account("327000")
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
                    ("description", "=", "VAT collected 19% Services"),
                    ("company_id", "=", company.id),
                ]
            )
            purch_serv_tax = self.env["account.tax"].search(
                [
                    ("description", "=", "VAT deductible 19% Services"),
                    ("company_id", "=", company.id),
                ]
            )
            _logger.info("Update and configure company %s data." % (company.name))
            company.write(
                {
                    "l10n_ro_accounting": True,
                    "account_storno": True,
                    "anglo_saxon_accounting": True,
                    "chart_template": "ro",
                    #"l10n_ro_stock_acc_price_diff": True,
                    "company_registry": "J35/1254/2018",
                    "phone": "0770816455",
                    "email": "contact@nexterp.ro",
                    "website": "https://nexterp.ro",
                    "l10n_ro_account_serv_sale_tax_id": sale_serv_tax,
                    "l10n_ro_account_serv_purchase_tax_id": purch_serv_tax,
                    "l10n_ro_property_stock_picking_payable_account_id": self.get_account("408000").id,
                    "l10n_ro_property_stock_picking_receivable_account_id": self.get_account("418000").id,
                    "l10n_ro_property_stock_usage_giving_account_id": self.get_account("803500").id,
                    "l10n_ro_property_stock_picking_custody_account_id": self.get_account("803300").id,
                    "l10n_ro_property_uneligible_tax_account_id": self.get_account("442820").id,
                    "l10n_ro_property_trade_discount_received_account_id": self.get_account("609000").id,
                    "l10n_ro_property_trade_discount_granted_account_id": self.get_account("709000").id,
                    "l10n_ro_property_vat_on_payment_position_id": afp_obj.search(
                        [
                            ("name", "=", "VAT collection system"),
                            ("company_id", "=", company.id),
                        ]
                    ),
                    "l10n_ro_property_inverse_taxation_position_id": afp_obj.search(
                        [
                            ("name", "=", "Reverse Tax Regime"),
                            ("company_id", "=", company.id),
                        ]
                    ),
                    "l10n_ro_no_signature_text": inv_text,
                }
            )
            # account_cash_basis_base_account_id

            _logger.info("Configure groups and options for company %s." % (company.name))
            config = self.env['res.config.settings'].with_company(company).create({
                "default_invoice_policy": "delivery",
                "group_multi_currency": True,
                "group_show_sale_receipts": True,
                "group_show_purchase_receipts": True,
                "group_sale_delivery_address": True,
                "group_uom": True,
                "group_discount_per_so_line": True,
                "group_proforma_sales": True,
                "group_stock_production_lot": True,
                "group_stock_multi_locations": True,
                # "extract_single_line_per_tax": False,
                # "module_sale_margin": True,
                # "module_account_invoice_extract": False,
                # "module_snailmail_account": False,
                # "module_partner_autocomplete": False,
                # "module_stock_sms": False,
                # "module_delivery": False,
            })
            config.flush_recordset()
            config.execute()

        del self.env.registry._auto_install_template
