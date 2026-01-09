from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_l10n_ro_anaf_europe_codes(self):
        europe_codes = []
        europe_group = self.env.ref("base.europe", raise_if_not_found=False)
        if not europe_group:
            europe_group = self.env["res.country.group"].search(
                [("name", "=", "Europe")], limit=1
            )
        if europe_group:
            europe_codes = europe_group.country_ids.mapped("code") + ["XI"]
        return europe_codes

    def _parse_anaf_vat_info(self, eu_countries=None):
        """Return tuple with split info (country_code, identifier_type and
        vat_number) from vat and country partner
        """
        if not eu_countries:
            eu_countries = self._get_l10n_ro_anaf_europe_codes()
        self.ensure_one()
        country_code = vat_number = vat_country_code = False
        identifier_type = "4"
        if (self.vat or self.country_id) and self.is_l10n_ro_record:
            vat_number = self.vat
            country_code = False
            if vat_number:
                country_code = self._split_vat(vat_number)[0].upper()
                vat_country_code = country_code
            if not country_code and self.country_id:
                country_code = self.country_id.code.upper()
            if (
                country_code
                and self.country_id
                and country_code != self.country_id.code.upper()
            ):
                country_code = self.country_id.code.upper()
            country_code = self._l10n_ro_map_vat_country_code(country_code)
            if country_code in eu_countries:
                identifier_type = "3"
            if country_code == "RO":
                if self.l10n_ro_vat_subjected:
                    identifier_type = "1"
                else:
                    identifier_type = "2"
            if not vat_country_code:
                vat_country_code = country_code
            if vat_number:
                vat_number = vat_number.replace(vat_country_code, "")
        if not self.is_company:
            identifier_type = "2"
        return vat_country_code, identifier_type, vat_number
