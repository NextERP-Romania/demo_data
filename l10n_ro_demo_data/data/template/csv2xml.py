import os

template_dir = os.path.dirname(os.path.realpath(__file__))
xml_dir = os.path.join(template_dir, "../")

# Generate res.partner XML

f = open(template_dir + "/res.partner.csv", "r")
new = open(xml_dir + "res_partner.xml", "w")

new.write(
    """<?xml version="1.0" encoding="utf-8" ?>
<odoo noupdate="1">"""
    + "\n"
)

lines = f.readlines()[1:]
for line in lines:
    line = line.replace('"', "")
    line = line.replace("\n", "")
    record = line.split(",")
    newline = """    <record id="%s" model="res.partner">
        <field name="name">%s</field>""" % (
        record[0],
        record[1],
    )
    if record[2]:
        newline += "\n"
        newline += """        <field name="parent_id" ref="%s"/>""" % record[2]
    newline += (
        """
        <field name="is_company">%s</field>"""
        % record[3]
    )
    if record[4]:
        newline += "\n"
        newline += """        <field name="vat">%s</field>""" % record[4]
    newline += """
        <field name="street">%s</field>
        <field name="city">%s</field>
        <field name="zip">%s</field>""" % (
        record[5],
        record[6],
        record[7],
    )

    if record[2]:
        newline += "\n"
        newline += """        <field name="state_id" ref="%s"/>""" % record[8]
    newline += """
        <field name="country_id" ref="%s"/>
        <field name="email">%s</field>
        <field name="phone">%s</field>
        <field name="l10n_ro_vat_subjected">%s</field>
        <field name="customer_rank">%s</field>
        <field name="supplier_rank">%s</field>
    </record> """ % (
        record[9],
        record[10],
        record[11],
        record[12],
        record[13],
        record[14],
    )
    new.write(newline + "\n")
new.write("""</odoo>""" + "\n")
f.close()


# Generate product category XML

f = open(template_dir + "/product.category.csv", "r")
new = open(xml_dir + "product_category.xml", "w")

new.write(
    """<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">"""
    + "\n"
)

lines = f.readlines()[1:]
for line in lines:
    line = line.replace('"', "")
    line = line.replace("\n", "")
    record = line.split(",")
    newline = """    <record id="%s"  model="product.category">
        <field name="parent_id" ref="%s"/>
        <field name="name">%s</field>
        <field name="property_cost_method">%s</field>
        <field name="property_valuation">%s</field>
        <field name="property_stock_account_input_categ_id"
               search="[('code', '=', '%s')]" model="account.account"/>
        <field name="property_stock_account_output_categ_id"
               search="[('code', '=', '%s')]" model="account.account"/>
        <field name="property_stock_valuation_account_id"
               search="[('code', '=', '%s')]" model="account.account"/>
        <field name="property_account_income_categ_id"
               search="[('code', '=', '%s')]" model="account.account"/>
        <field name="property_account_expense_categ_id"
               search="[('code', '=', '%s')]" model="account.account"/>
    </record> """ % (
        record[0],
        record[1],
        record[2],
        record[3],
        record[4],
        record[5],
        record[6],
        record[7],
        record[8],
        record[9],
    )
    new.write(newline + "\n")
new.write("""</odoo>""" + "\n")
f.close()

# Generate product template XML
f = open(template_dir + "/product.product.csv", "r")
new = open(xml_dir + "product_product.xml", "w")

new.write(
    """<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">"""
    + "\n"
)

lines = f.readlines()[1:]
for line in lines:
    line = line.replace('"', "")
    line = line.replace("\n", "")
    record = line.split(",")
    newline = """    <record id="%s"  model="product.product">
        <field name="name">%s</field>
        <field name="categ_id" search="[('name', '=', '%s')]" model="product.category"/>
        <field name="type">%s</field>
        <field name="uom_id" ref="%s"/>
        <field name="uom_po_id" ref="%s"/>
        <field name="default_code">%s</field>""" % (
        record[0],
        record[1],
        record[2],
        record[3],
        record[4],
        record[5],
        record[6],
    )
    if record[7]:
        newline += (
            """
        <field name="barcode">%s</field>"""
            % record[7]
        )
    newline += """
        <field name="list_price">%s</field>
        <field name="taxes_id" search="[('name', '=', '%s')]" model="account.tax"/>
        <field name="supplier_taxes_id" search="[('name', '=', '%s')]" model="account.tax"/>
    """ % (
        record[8],
        record[9],
        record[10],
    )
    if record[11]:
        newline += """    <field name="seller_ids" eval="[(0, 0, {'partner_id': ref('l10n_ro_demo_data.%s'), 'price': %s})]"/>
        """ % (
            record[11],
            record[12] if record[12] else 0,
        )
    newline += """</record> """
    new.write(newline + "\n")
new.write("""</odoo>""" + "\n")
f.close()

# Generate sale order XML
f = open(template_dir + "/sale.order.csv", "r")
new = open(xml_dir + "sale_order.xml", "w")

new.write(
    """<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">"""
    + "\n"
)

lines = f.readlines()[1:]
for line in lines:
    line = line.replace('"', "")
    line = line.replace("\n", "")
    record = line.split(",")
    newline = """    <record id="%s"  model="sale.order">
        <field name="name">%s</field>
        <field name="partner_id" ref="%s"/>
        <field name="fiscal_position_id" ref="%s"/>
        <field name="order_line"
        eval="[(0, 0, {'product_id': ref('%s'), 'product_uom_qty': %s, 'price_unit': %s})]"/>
    </record>""" % (
        record[0],
        record[1],
        record[2],
        record[3],
        record[4],
        record[5],
        record[6],
    )
    new.write(newline + "\n")
new.write("""</odoo>""" + "\n")
f.close()
