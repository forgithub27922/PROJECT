import base64

import xlrd
from odoo import fields, models, api


class ImportProducts(models.TransientModel):
    _name = 'import.products.wizard'
    _description = 'Import Products Wizard'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    import_type = fields.Selection([('import_sale', 'Import Sale'), (
        'import_service', 'Import Service')], string='Import Type', default='import_sale')

    def action_import_xlsx(self):

        self.ensure_one()

        blob_data = base64.b64decode(self.data)
        import_excel_file = xlrd.open_workbook(
            file_contents=blob_data, encoding_override='UTF8')
        excel_sheet = import_excel_file.sheet_by_index(0)

        for row_index in range(0, excel_sheet.nrows):
            if row_index == 0:
                continue

            row_data = excel_sheet.row_values(row_index)
            row_data = [str(rec) for rec in row_data]
            self.create_product_from_xlsx_rows(row_data)

        # import_excel_file.close()
        return True

    def category(self, input):
        res = {}
        if input:
            res_ctg_id = None

            ctg_names = ''.join(input).split('/')
            ctg_names = [el.strip() for el in ctg_names]
            ctg_ids = []

            ctg_level_counter = 0

            for ctg_name in ctg_names:
                ctg_domain = [('name', '=', ctg_name)]
                if ctg_level_counter > 0:
                    ctg_domain.append(
                        ('parent_id', 'in', ctg_ids[ctg_level_counter - 1]))

                name_ids = self.env['product.category'].search(ctg_domain)

                if not name_ids:
                    break

                ctg_level_counter += 1
                ctg_ids.append(name_ids.ids)

            for ids in reversed(ctg_ids):
                if len(ids) == 1:
                    res_ctg_id = ids[0]
                    break

            if res_ctg_id:
                res['categ_id'] = res_ctg_id
            # else:
            # self.response_msg.append(_('No matching product or category!'))

        return res

    def create_product_from_xlsx_rows(self, row):
        loop_counter = 0
        update_counter = 0
        create_counter = 0
        failed_counter = 0
        loop_counter = loop_counter + 1
        print(">> product %s" % (row[0]))
        # print row['supplier']
        partner_cell = row[3].partition(", ")
        spare_partner = partner_cell[0]
        spare_contact = partner_cell[2]
        internal_category = row[6].rpartition(" / ")
        striped_internal_cat = internal_category[2].strip()
        try:
            rrp_price = float(row[11].replace(',', '.'))
            if rrp_price == 0:
                rrp_price = 9999.99
        except ValueError:
            rrp_price = 0
        try:
            list_price = float(row[5].replace(',', '.'))
            if list_price == 0:
                list_price = 9999.99
        except ValueError:
            list_price = 9999.99
        try:
            standard_price = float(row[4].replace(',', '.'))
            if standard_price == 0:
                standard_price = 9999.99
        except ValueError:
            standard_price = 9999.99

        import_type_invocing_policy_map = {
            'import_sale': 'order',
            'import_service': 'delivery'
        }

        control_purchase_bills_map = {
            'import_sale': 'purchase',
            'import_service': 'receive'
        }

        if isinstance(standard_price, float):
            res_products = self.env['product.product'].search(
                [('default_code', '=', row[0])])
            warranty_type_id = self.env['product.warranty.type'].search(
                [('name', '=', row[20])])
            parent_partner = self.env['res.partner'].search(
                [('name', '=', spare_partner)], limit=1).ids
            contact_partner = self.env['res.partner'].search(
                [('name', '=', spare_contact), ('parent_id', 'in', parent_partner)], limit=1)
            product_brand_id = self.env[
                'grimm.product.brand'].search([('name', '=', row[2])])
            internal_category_id = self.env['product.category'].search(
                [('name', '=', striped_internal_cat)])
            if not internal_category_id:
                internal_category_id = self.category(internal_category)
                if internal_category_id:
                    internal_category_id = self.env['product.category'].create({
                        'name': striped_internal_cat,
                        'parent_id': internal_category_id['categ_id']
                    }).id
                else:
                    internal_category_id = self.env['product.category'].create({
                        'name': striped_internal_cat
                    }).id

            else:
                internal_category_id = internal_category_id[0].id
            if row[7] == '1':
                spare_part = True
            else:
                spare_part = False
            if row[8] == '1':
                service_part = True
            else:
                service_part = False

            if row[30]:
                attribute_set = self.env['product.attribute.set'].search(
                    [('name', '=', row[30])], limit=1).id
            else:
                attribute_set = False
            # If product found
            if len(res_products) > 0:
                product_id = res_products[0]
                print(">> product_id %s" % (product_id))
                # output.write('update product %s\n' % row['supplier_default_code'])
                update_counter = update_counter + 1
                data_prod = {
                    'rrp_price': rrp_price or False,
                    'list_price': list_price or False,
                    'standard_price': standard_price,
                    'name': row[1],
                    'description': row[23] or False,
                    'description_sale': row[24] or False,
                    'description_purchase': row[25] or False,
                    'default_code': row[0] or False,
                    'warranty': row[21],
                    'invoice_policy': import_type_invocing_policy_map.get(self.import_type, False),
                    'purchase_method': control_purchase_bills_map.get(self.import_type, False),
                    'warranty_type': len(warranty_type_id) == 1 and warranty_type_id[0].id or False,
                    'product_brand_id': product_brand_id.id,
                    'categ_id': internal_category_id,
                    'is_spare_part': spare_part,
                    'is_service_part': service_part,
                    'type': 'product',
                    'weight': row[13] or False,
                    'net_weight': row[14] or False,
                    'volume': row[15] or False,
                    'height': row[16] or False,
                    'width': row[17] or False,
                    'depth': row[18] or False,
                }
                if row[26] == '1.0':
                    slr_id = self.env['stock.location.route'].search(
                        [('name', 'ilike', 'Make To Order')], limit=1)
                    print(slr_id)
                    make_to_order = [(4, 1)]
                    data_prod.update({'route_ids': make_to_order})
                product_product = product_id.write(data_prod)
                if product_product != True:
                    failed_counter = failed_counter + 1
                    #     output.write('failed update %s\n' % row['supplier_default_code'])

            # product not found
            else:
                # output.write('new product %s\n' % row['supplier_default_code'])
                create_counter = create_counter + 1
                data_template = {
                    'sale_ok': True,
                    'purchase_ok': True,
                    'description': row[23] or False,
                    'description_sale': row[24] or False,
                    'description_purchase': row[25] or False,
                    'active': True,
                    'name': row[1],
                    'type': 'product',
                    'invoice_policy': import_type_invocing_policy_map.get(self.import_type, False),
                    'product_brand_id': product_brand_id.id,
                    'is_spare_part': spare_part,
                    'is_service_part': service_part,
                    'purchase_method': control_purchase_bills_map.get(self.import_type, False),
                    'taxes_id': [(6, 0, [1])],
                    'supplier_taxes_id': [(6, 0, [1])],
                    'has_variants': False,
                    'price_calculation': 'standard',
                    'default_code': row[0],
                    'rrp_price': rrp_price,
                    'list_price': list_price,
                    'standard_price': standard_price,
                    'categ_id': internal_category_id,
                    'warranty': row[21],
                    'warranty_type': len(warranty_type_id) == 1 and warranty_type_id[0].id or False,
                    'weight': row[13] or False,
                    'net_weight': row[14] or False,
                    'volume': row[15] or False,
                    'height': row[16] or False,
                    'width': row[17] or False,
                    'depth': row[18] or False,
                    'attribute_set_id': attribute_set,
                }
                if row[26] == '1.0':
                    slr_id = self.env['stock.location.route'].search(
                        [('name', 'ilike', 'Make To Order')], limit=1)
                    print(slr_id)
                    make_to_order = [(4, 1)]
                    data_template.update({'route_ids': make_to_order})
                product_template = self.env[
                    'product.template'].create(data_template)

                if contact_partner:
                    data_supplier = {
                        'name': contact_partner[0].id,
                        'product_name': row[10],
                        'product_code': row[0],
                        'delay': 1,
                        'min_qty': 1.00,
                        'price': standard_price,
                        'product_tmpl_id': product_template.id,
                    }
                    product_supplier = self.env[
                        'product.supplierinfo'].create(data_supplier)

    def create_products_from_array(self, array):
        loop_counter = 0
        update_counter = 0
        create_counter = 0
        failed_counter = 0
        for row in array:
            loop_counter = loop_counter + 1
            print(">> product %s\n" % (row['supplier_default_code']))
            # print row['supplier']
            partner_cell = row['supplier'].partition(", ")
            spare_partner = partner_cell[0]
            spare_contact = partner_cell[2]
            internal_category = row['internal_category'].rpartition(" / ")
            striped_internal_cat = internal_category[2].strip()
            try:
                rrp_price = float(row['rrp_price'].replace(',', '.'))
                if rrp_price == 0:
                    rrp_price = 9999.99
            except ValueError:
                rrp_price = 0
            try:
                list_price = float(row['list_price'].replace(',', '.'))
                if list_price == 0:
                    list_price = 9999.99
            except ValueError:
                pass

            try:
                standard_price = float(row['standard_price'].replace(',', '.'))
            except ValueError:
                standard_price = 0
            if standard_price == 0:
                standard_price = 9999.99
            if isinstance(standard_price, float):
                res_products = self.env['product.product'].search(
                    [('default_code', '=', row['supplier_default_code'])])
                warranty_type_id = self.env['product.warranty.type'].search(
                    [('name', '=', row['warranty_type'])])
                parent_partner = self.env['res.partner'].search(
                    [('name', '=', spare_partner)])
                contact_partner = self.env['res.partner'].search(
                    [('name', '=', spare_contact)])
                product_brand_id = self.env['grimm.product.brand'].search(
                    [('name', '=', row['product_brand'])])
                internal_category_id = self.env['product.category'].search(
                    [('name', '=', striped_internal_cat)])
                if not internal_category_id:
                    internal_category_id = self.category(internal_category)
                    self.env['product.category'].create(internal_category_id)

                else:
                    internal_category_id = internal_category_id[0].id
                if row['spare_part'] == '1':
                    spare_part = True
                else:
                    spare_part = False
                if row['service_part'] == '1':
                    service_part = True
                else:
                    service_part = False
                # If product found
                if len(res_products) > 0:
                    product_id = res_products[0]
                    print(">> product_id %s" % (product_id))
                    update_counter = update_counter + 1
                    data_prod = {
                        'rrp_price': rrp_price or False,
                        'list_price': list_price or False,
                        'standard_price': standard_price,
                        'name': row['name'],
                        'description': row['description'] or False,
                        'description_sale': row['description_sale'] or False,
                        'description_purchase': row['description_delivery'] or False,
                        'default_code': row['supplier_default_code'] or False,
                        'warranty': row['warranty'],
                        'warranty_type': len(warranty_type_id) == 1 and warranty_type_id[0] or False,
                        'product_brand_id': product_brand_id.id,
                        'categ_id': internal_category_id,
                        'is_spare_part': spare_part,
                        'is_service_part': service_part,
                        'type': 'product',
                        'weight': row['weight'] or False,
                        'net_weight': row['net_weight'] or False,
                        'volume': row['volume'] or False,
                        'height': row['height'] or False,
                        'width': row['width'] or False,
                        'depth': row['depth'] or False,
                    }
                    product_product = self.env[
                        'product.product'].write(data_prod)
                    if product_product != True:
                        failed_counter = failed_counter + 1
                    #     output.write('failed update %s\n' % row['supplier_default_code'])

                # product not found
                else:
                    # output.write('new product %s\n' % row['supplier_default_code'])
                    create_counter = create_counter + 1
                    data_template = {
                        'sale_ok': True,
                        'purchase_ok': True,
                        'description': row['description'] or False,
                        'description_sale': row['description_sale'] or False,
                        'description_purchase': row['description_delivery'] or False,
                        'active': True,
                        'name': row['name'],
                        'type': 'product',
                        'invoice_policy': 'order',
                        'product_brand_id': product_brand_id.id,
                        'is_spare_part': spare_part,
                        'is_service_part': service_part,
                        'purchase_method': 'purchase',
                        'taxes_id': [(6, 0, [1])],
                        'supplier_taxes_id': [(6, 0, [1])],
                        'has_variants': False,
                        'price_calculation': 'standard',
                        'default_code': row['supplier_default_code'],
                        'rrp_price': rrp_price,
                        'list_price': list_price,
                        'standard_price': standard_price,
                        'categ_id': internal_category_id,
                        'warranty': row['warranty'],
                        'warranty_type': len(warranty_type_id) == 1 and warranty_type_id[0] or False,
                        'weight': row['weight'] or False,
                        'net_weight': row['net_weight'] or False,
                        'volume': row['volume'] or False,
                        'height': row['height'] or False,
                        'width': row['width'] or False,
                        'depth': row['depth'] or False,
                    }
                    product_template = self.env[
                        'product.template'].create(data_template)
