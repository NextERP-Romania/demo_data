# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def install_demo_data(self):
        self.ensure_one()
        self.update_company_config()
        self.env["nexterp.demodata"].install_demo_data(company=self)

    def update_company_config(self):
        self.ensure_one()
        acc_obj = self.env["account.account"]
        afp_obj = self.env["account.fiscal.position"]
        for company in self:
            avans_prod = self.env.ref(
                "l10n_ro_demo_data.nexterp_demo_product_1994", raise_if_not_found=False
            )
            if not avans_prod:
                avans_prod = self.env["product.product"].search(
                    [
                        ("name", "=", "Avans Clienti/Furnizori"),
                        ("company_id", "=", company.id),
                    ]
                )
                if not avans_prod:
                    avans_prod = self.env["product.product"].create(
                        {
                            "name": "Avans Clienti/Furnizori",
                            "type": "service",
                            "categ_id": self.env.ref("product.product_category_all").id,
                        }
                    )
            if avans_prod:
                avans_prod.write(
                    {
                        "property_account_income_id": acc_obj.search(
                            [("code", "=", "419000"), ("company_id", "=", company.id)]
                        ),
                        "property_account_expense_id": acc_obj.search(
                            [("code", "=", "409000"), ("company_id", "=", company.id)]
                        ),
                    }
                )
            inv_text = (
                "Factura circulă fără semnătură și ștampilă conform legii "
                "227/2015, regula 319, paragraful 29."
            )
            # Add services taxes to configuration
            # sale_serv_tax = self.env["account.tax"].search(
            #     [
            #         ("name", "=", "TVA colectat 19% Servicii"),
            #         ("company_id", "=", company.id),
            #     ]
            # )
            # purch_serv_tax = self.env["account.tax"].search(
            #     [
            #         ("name", "=", "TVA deductibil 19% Servicii"),
            #         ("company_id", "=", company.id),
            #     ]
            # )
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
                    # "account_serv_sale_tax_id": sale_serv_tax
                    # if sale_serv_tax
                    # else False,
                    # "account_serv_purchase_tax_id": purch_serv_tax
                    # if purch_serv_tax
                    # else False,
                    "l10n_ro_property_stock_picking_payable_account_id": acc_obj.search(
                        [("code", "=", "408000"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_stock_picking_receivable_account_id": acc_obj.search(
                        [("code", "=", "418000"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_stock_usage_giving_account_id": acc_obj.search(
                        [("code", "=", "803500"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_stock_picking_custody_account_id": acc_obj.search(
                        [("code", "=", "803300"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_uneligible_tax_account_id": acc_obj.search(
                        [("code", "=", "442820"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_trade_discount_received_account_id": acc_obj.search(
                        [("code", "=", "609000"), ("company_id", "=", company.id)]
                    ),
                    "l10n_ro_property_trade_discount_granted_account_id": acc_obj.search(
                        [("code", "=", "709000"), ("company_id", "=", company.id)]
                    ),
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
            "module_sale_margin": True,
            "deposit_default_product_id": avans_prod.id,
            "extract_single_line_per_tax": False,
            "module_account_invoice_extract": False,
            "module_snailmail_account": False,
            "module_partner_autocomplete": False,
            "stock_move_sms_validation": False,
        }
        if acs_ids:
            acs_ids.write(values)
