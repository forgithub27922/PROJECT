from odoo import models, fields, api, _
from tempfile import TemporaryFile, NamedTemporaryFile
import csv
from odoo.exceptions import UserError
import base64
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class UpdateBrandDescWizard(models.TransientModel):
    _name = 'update.brand.desc.wizard'
    _description = 'Update Brand Description Wizard'

    csv_file = fields.Binary('Browse File')
    sku_filename = fields.Char('File name')
    upload_info = fields.Html("Upload Information")
    download_link = fields.Html('Download Link')
    only_gev = fields.Boolean('GEV Only', help='Update only GEV products')

    @api.onchange('csv_file')
    def filename_change(self):
        self.sku_filename = self.sku_filename
        if self.sku_filename:
            try:
                temp = NamedTemporaryFile()
                temp.write(base64.b64decode(self.csv_file))
                temp.seek(0)
                reader = csv.reader(open(temp.name), delimiter=';')

                for row in reader:
                    if len(row) != 5:
                        raise UserError(_('The CSV syntax foes not match the expected syntax'))

            except Exception as e:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload a valid CSV file.</h2></center>")
                raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload a CSV file.</h2></center>")

    def import_brand_desc(self):
        try:
            temp = NamedTemporaryFile()
            temp.write(base64.b64decode(self.csv_file))
            temp.seek(0)

            count, gev_ct = 0, 0
            lst_products = []

            ct = 0
            reader = csv.reader(open(temp.name), delimiter=';')
            for row in reader:

                ct += 1
                # sku = [sku_rec.product_code for sku_rec in prod.sudo().seller_ids if
                #        sku_rec.product_code and sku_rec.name.id not in [1, 83602, 7393, 9567, 33147, 14655, 24357, 24404]]
                # operator = '=like' if self.only_gev else '!='
                val = 'GEV-%' if self.only_gev else '%' + row[2] + '%'
                if len(row) != 5:
                    raise UserError(_('The CSV syntax foes not match the expected syntax'))
                prods = self.env['product.template'].search(
                    [('default_code', '=like', val), ('seller_ids', '!=', False)], limit=1)
                # sorted_prod = prods.sorted(key=lambda s: s.id)
                for prod in prods:
                    _logger.info(
                        '[PDF KATALOG] Product being checked: %d and the count: %d / %d ' % (prod.id, ct, len(prods)))
                    sku = False
                    if prod.default_code:
                        sku = prod.default_code
                        # vendor = [vendor for vendor in prod.sudo().seller_ids if
                        #               vendor.product_code and vendor.name.id in [1396, 42638, 42641, 4426, 3730, 91012, 58609, 42639]]
                        # sku = 'GEV-' + row[1]
                        # gev_ct += 1

                        # if prod.default_code.startswith('GEV-') and row[1] in prod.default_code:
                        #     sku = prod.default_code
                        #     gev_ct += 1
                        #
                        # if prod.default_code and not sku and row[2] in prod.default_code:
                        #     sku = prod.default_code

                    if sku:
                        _logger.info('[PDF KATALOG] PRODUCT ID %d and the SKU %s' % (prod.id, sku))
                        prod.prod_name, prod.description = row[3], row[3]

                        if row[4]:
                            modell_text = row[4].replace('...(Weitere Modelle finden Sie in unserem Webshop)', '')
                            passend_fuer_marke = self.env['product.attribute'].search([('name', '=', 'Passend für Marke')], limit=1)
                            ersatzteilkateg = self.env['product.attribute'].search(
                                [('name', '=', 'Ersatzteilkategorie')], limit=1)
                            if prod.property_set_id:
                                attr_ids = prod.property_set_id.product_attribute_ids
                                lst_attrs = [pattr for pattr in attr_ids.ids]
                                if passend_fuer_marke.id not in lst_attrs:
                                    lst_attrs.append(passend_fuer_marke.id)
                                    prod.property_set_id.product_attribute_ids = [(6, 0, lst_attrs)]

                                if ersatzteilkateg.id not in lst_attrs:
                                    lst_attrs.append(ersatzteilkateg.id)
                                    prod.property_set_id.product_attribute_ids = [(6, 0, lst_attrs)]

                                if not passend_fuer_marke.value_ids:
                                    passend_fuer_marke.value_ids = [(0, 0, dict(name=modell_text))]

                                print('ERSATZ ', ersatzteilkateg.value_ids.ids)
                                ersatz_val_ids = self.env['product.attribute.value'].browse(ersatzteilkateg.value_ids.ids)
                                ersatz_val_names = [val.name for val in ersatz_val_ids]
                                device_name = row[3].split(' ')[0]
                                if device_name not in ersatz_val_names:
                                    ersatzteilkateg.value_ids = [(0, 0, dict(name=device_name))]

                                attr_val_exists_pass = [attr for attr in prod.shopware_property_ids if
                                 attr.attribute_id.id == passend_fuer_marke.id and [val for val in attr.value_ids if
                                                                                    val.name == modell_text]]

                                if not attr_val_exists_pass:
                                    val_rec = [aval.id for aval in passend_fuer_marke.value_ids if aval.name == modell_text]
                                    prod.shopware_property_ids = [(0, 0, dict(attribute_id=passend_fuer_marke.id, value_ids=[(6, 0, val_rec)]))]
                                    print('Attribute Updated 1')

                                attr_val_exists_cat = [attr for attr in prod.shopware_property_ids if
                                                   attr.attribute_id.id == ersatzteilkateg.id and [val for val in
                                                                                                      attr.value_ids if
                                                                                                      val.name == device_name]]

                                if not attr_val_exists_cat:
                                    val_rec = [aval.id for aval in ersatzteilkateg.value_ids if aval.name == device_name]
                                    prod.shopware_property_ids = [
                                        (0, 0, dict(attribute_id=ersatzteilkateg.id, value_ids=[(6, 0, val_rec)]))]
                                    print('Attribute Updated 2')
                            else:
                                #self.env.user.notify_warning(_(
                                #    'Please assign a property set for the product %s with ID %d' % (prod.name, prod.id)), _("No Propertyset Found"), True)
                                raise UserError(
                                 _('Please assign a property set for the product %s with ID %d' % (prod.name, prod.id)))

                        lst_products.append([prod.id, prod.name, row[3], sku])
                        count += 1
                        _logger.info('[PDF KATALOG] Count: %d; LST PRODS: %s' % (count, lst_products))
                        # break
                # print(ct2)
                #         if count >= 5:
                #             break
                #
                # if count >= 16:
                #     break

            #self.env.user.notify_info('Number of records updated = %d' % count, 'Number of records updated', True)
            download_file = NamedTemporaryFile()
            with open(download_file.name, mode='w') as download:
                download_writer = csv.writer(download, delimiter=';')
                download_writer.writerow(['ID', 'Actual Name', 'Proposed Name', 'SKU'])
                for csv_prod in lst_products:
                    download_writer.writerow(csv_prod)
            data = open(download_file.name, "rb").read()
            encoded = base64.b64encode(data)
            attach_id = self.env["ir.attachment"].create(
                {"name": 'pdf_Katalog_%s.csv' % str(datetime.now()),
                 "datas": encoded,
                 "public": True,
                 "res_model": "update.brand.desc.wizard",
                 "datas_fname": "products.csv"})
            self.download_link = "<a href='/web/content/" + str(
                attach_id.id) + "/download_result.csv' class='btn btn-info btn-sm'><span class='glyphicon glyphicon-save'></span> Download CSV</a>"

            tbody = ["<tr><td><a href='#home&amp;id=" + str(pr[0]) + "&view_type=form&model=product.template&menu_id=839&action=111' class='open_tab_widget fa fa-eye' data-original-title='' title='' target='_blank'></a></td><td>" + pr[1] + "</td><td>" + pr[2] + "</td><td>" + pr[3] + "</td></tr>" for pr in lst_products]
            table = "<table class='table table-bordered'><thead><tr><td></td><td>Actual Name</td><td>Proposed Name</td><td>SKU</td></tr></thead><tbody>" + "".join(tbody) + "</tbody></table>"

            return {
                    "type": "ir.actions.act_window",
                    "res_model": "show.product.wizard",
                    "views": [[self.env.ref('grimm_product_stock_ext.show_product_wizard_form').id, "form"]],
                    "context": {'default_download_link': self.download_link, 'default_prod_table': table},
                    "target": "new",
                    "flags": {"initial_mode": "readonly"}
                }
        except Exception as e:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload a valid CSV file.</h2></center>")
            raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))


class ShowProductWizard(models.TransientModel):
    _name = 'show.product.wizard'
    _description = 'Show product wizard'

    download_link = fields.Html("Download CSV")
    prod_table = fields.Html("Products")
