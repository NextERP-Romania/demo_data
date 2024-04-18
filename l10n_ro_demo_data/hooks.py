# Copyright 2020 NextERP Romania SRL
# License OPL-1.0 or later

from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    cr.execute(
        """
    UPDATE res_company
    SET anglo_saxon_accounting=True,
        l10n_ro_accounting=True,
        l10n_ro_stock_acc_price_diff=True
    """
    )

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env["res.company"].search([])
    company[0].install_demo_data()
