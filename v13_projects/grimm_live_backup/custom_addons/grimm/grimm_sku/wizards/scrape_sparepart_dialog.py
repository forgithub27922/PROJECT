# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
import requests
from bs4 import BeautifulSoup
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class ScrapeSparepartDialog(models.TransientModel):
    _name = 'scrape.sparepart.dialog'
    _description = 'Scrape Sparepart Dialog'

    sku_vendor_codes = fields.Char('Product Vendor Codes', required=True)
    brand = fields.Char('Venor Code Name', help='Enter a brand name only when the product brand is different from the target.', required=True)
    source = fields.Selection(selection=[('GP', 'Gastroparts (GP)'), ('MO', 'Mercateo (MO)')], string='Source',
                              default='GP', required=True)
    all_sources = fields.Boolean('All Sources', help="Scrapes through all the sources one by one")

    def fetch_next_row_param_sib(self, ele):
        return ele.next_sibling

    def fetch_data_gastroparts(self, sku_no, prod_id, brand):
        page = requests.get("https://www.gastroparts.com/partner_towary.php?szukaj=%s" % sku_no)
        soup = BeautifulSoup(page.content, 'html.parser')
        link_lst = soup.find_all('a', class_='lista-link')
        link_lst = list(set([link.get('href') for link in link_lst]))
        lst_spareparts = []
        for link in link_lst:
            has_sku = False
            link = link.replace('pl', 'de')
            spare_part_html = BeautifulSoup(requests.get(link).content, 'html.parser')
            oem_teilnummer = spare_part_html.find_all('div', class_='row-td-header-title')
            has_oem_teil = [list(heading.children)[0].get_text() for heading in oem_teilnummer if
                            list(heading.children)[0].get_text() == 'OEM-Teilenummer']
            if has_oem_teil:
                lst_tech_details = spare_part_html.find_all('div', class_='row-td-parametry')
                dict_tech_details = {}
                for pair in lst_tech_details:
                    key, value = list(pair.children)[0], list(pair.children)[1]
                    if key.get_text().rstrip() not in dict_tech_details:
                        if prod_id:
                            prod = self.env['product.template'].browse(prod_id)

                            if not brand:
                                if sku_no in value.get_text().rstrip().split(
                                        ', ') and prod.product_brand_id and prod.product_brand_id.name.upper() == key.get_text().rstrip():
                                    has_sku = True
                                if sku_no in value.get_text().rstrip().split(
                                        ', ') and prod.product_brand_id and prod.product_brand_id.name == "PARTENICS":
                                    has_sku = True
                            else:
                                if sku_no in value.get_text().rstrip().split(
                                        ', ') and brand.upper() == key.get_text().rstrip():
                                    has_sku = True

                        dict_tech_details.update({key.get_text().rstrip(): value.get_text()})

                dict_oem_num = {}
                lst_oem_teilenummer = spare_part_html.find_all('div', class_='row-td-header-title')
                oem_teile_ele = [oem_part for oem_part in lst_oem_teilenummer if
                                 list(oem_part.children)[0].get_text() == 'OEM-Teilenummer']
                for row_oem_ele in oem_teile_ele:
                    k_oem, v_oem = list(row_oem_ele.next_sibling.children)[0], list(row_oem_ele.next_sibling.children)[
                        1]
                    dict_oem_num.update({k_oem.get_text().rstrip(): v_oem.get_text()})

                if oem_teile_ele:
                    next_sib = self.fetch_next_row_param_sib(oem_teile_ele[0])
                    while True:
                        if 'row-td-parametry' in list(next_sib.next_sibling)[0].parent.get('class'):
                            k_oem, v_oem = list(next_sib.next_sibling.children)[0], \
                                           list(next_sib.next_sibling.children)[1]
                            dict_oem_num.update({k_oem.get_text().rstrip(): v_oem.get_text()})
                            next_sib = list(next_sib.next_sibling)[0].parent
                        else:
                            break

                dict_passend_modell = {}
                lst_passend_modell = spare_part_html.find_all('div', class_='row-td-header-title')
                passend_modell_ele = [oem_part for oem_part in lst_passend_modell if
                                      list(oem_part.children)[0].get_text() == 'passend für Modell']
                for row_passend_ele in passend_modell_ele:
                    k_passend, v_passend = list(row_passend_ele.next_sibling.children)[0], \
                                           list(row_passend_ele.next_sibling.children)[
                                               1]
                    dict_passend_modell.update({k_passend.get_text().rstrip(): v_passend.get_text()})

                if passend_modell_ele:
                    next_sib_passend = self.fetch_next_row_param_sib(passend_modell_ele[0])
                    while True:
                        if 'row-td-parametry' in list(next_sib_passend.next_sibling)[0].parent.get('class'):
                            k_passend, v_passend = list(next_sib_passend.next_sibling.children)[0], \
                                                   list(next_sib_passend.next_sibling.children)[1]
                            dict_passend_modell.update({k_passend.get_text().rstrip(): v_passend.get_text()})
                            next_sib_passend = list(next_sib_passend.next_sibling)[0].parent
                        else:
                            break

                filteredTechDtl = {}
                setTectDtl = set(dict_tech_details)
                setOemDtl = set(dict_oem_num)
                setPassendModell = set(dict_passend_modell)
                for item in setTectDtl.difference(setOemDtl):
                    filteredTechDtl.update({item: dict_tech_details[item]})

                filteredTechDtl_final = {}
                for item in set(filteredTechDtl).difference(setPassendModell):
                    filteredTechDtl_final.update({item: filteredTechDtl[item]})

                sparepart = {
                    'sku': sku_no,
                    'name': spare_part_html.find('h1', class_='product-header-bold').get_text(),
                    'technical_details': filteredTechDtl_final,
                    'oem_details': dict_oem_num,
                    'fits_to': dict_passend_modell,
                    'source': 'GP'
                }

            if has_sku:
                lst_spareparts.append(sparepart)

        return lst_spareparts

    def fetch_data_mercateo(self, sku_no, prod_id, brand):
        prod = self.env['product.template'].browse(prod_id)
        lst_spareparts = []
        if not prod.product_brand_id and not brand:
            return lst_spareparts

        brand = brand.lower() if brand else prod.product_brand_id.name.lower()
        page = requests.get("http://www.mercateo.com/q?query=%s+%s" % (sku_no, brand))
        soup = BeautifulSoup(page.content, 'html.parser')
        link_lst = soup.find_all('a', class_='plvistedeffect')
        link_lst = list(set([link.get('href') for link in link_lst]))

        for link in link_lst:
            has_sku = False
            dict_tech_details = {}
            spare_part_html = BeautifulSoup(requests.get('http://www.mercateo.com' + link).content, 'html.parser')
            lst_tech_details = spare_part_html.find_all('tr', class_=['B2', 'B14'])
            brand_sku = spare_part_html.find_all('table', class_='BD15')
            td_brand_sku = [tab.find('td', class_='BD02') for tab in brand_sku if tab.find_all('td', class_='BD02')][0]
            val_spans = td_brand_sku.find_all('span', class_='')
            vals = [span.get_text().lstrip().lower() for span in val_spans if val_spans]

            if brand in vals and sku_no in vals:
                has_sku = True

            dict_tech_details.update({'EAN/GTIN': vals[-1]})

            for keyval in lst_tech_details:
                if len(keyval.get('class')) == 1:
                    #     condition to avoid fetching unwanted rows
                    key = [pair.find('div').get_text() for pair in list(keyval.children) if
                           len(pair.find('div').get('class')) == 2][0]
                    key = key.replace(':', '')
                    val = [pair.find('div').get_text() for pair in list(keyval.children) if
                           len(pair.find('div').get('class')) == 1][0]
                    dict_tech_details.update({key: val})

            sparepart = {
                'sku': sku_no,
                'name': spare_part_html.find('h1', class_='fs_3').get_text(),
                'technical_details': dict_tech_details,
                'oem_details': {},
                'fits_to': {},
                'source': 'MO'
            }

            if has_sku:
                prod.ean_number = vals[-1]
                lst_spareparts.append(sparepart)

        return lst_spareparts

    def insert_or_update_sparepart(self, spare_parts, prod_id):
        for map in spare_parts:
            name, technical_details, sku, oem_details, source, fits_to = map.get('name'), map.get('technical_details'), map.get(
                'sku'), map.get('oem_details'), map.get('source'), map.get('fits_to')
            SkuProdName = self.env['sku.product.name']
            sku_prod_name = SkuProdName.search(
                [('name', '=', name), ('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod_id)])
            vals_name = {
                'name': name,
                'sku': sku,
                'source': source,
                'product_id': prod_id
            }
            if sku_prod_name:
                sku_prod_name.write({'name': name})
            else:
                SkuProdName.create(vals_name)

            SkuTechDtls = self.env['sku.technical.details']
            for k, v in technical_details.items():
                vals_tdl = {
                    'key': k,
                    'value': v,
                    'sku': sku,
                    'source': source,
                    'product_id': prod_id
                }
                tech_dtl = SkuTechDtls.search(
                    [('sku', '=', sku), ('key', '=', k), ('source', '=', source), ('product_id', '=', prod_id)])
                if tech_dtl:
                    tech_dtl.write({'value': v})
                else:
                    res = SkuTechDtls.create(vals_tdl)

            SkuOemDtls = self.env['sku.oem.details']
            for k, v in oem_details.items():
                vals_odl = {
                    'brand': k,
                    'brand_sku': v,
                    'sku': sku,
                    'source': source,
                    'product_id': prod_id
                }
                oem_dtl = SkuOemDtls.search(
                    [('sku', '=', sku), ('brand', '=', k), ('source', '=', source), ('product_id', '=', prod_id)])
                if oem_dtl:
                    oem_dtl.write({'brand_sku': v})
                else:
                    SkuOemDtls.create(vals_odl)

            SkuFitsTo = self.env['sku.fits.to']
            for k, v in fits_to.items():
                vals_fits_to = {
                    'key': k,
                    'value': v,
                    'sku': sku,
                    'source': source,
                    'product_id': prod_id
                }
                fit_to = SkuFitsTo.search(
                    [('sku', '=', sku), ('key', '=', k), ('source', '=', source), ('product_id', '=', prod_id)])
                if fit_to:
                    fit_to.write({'value': v})
                else:
                    SkuFitsTo.create(vals_fits_to)

            return True

    def scrape_sparepart_action(self):
        active_ids = self.env.context.get('active_ids')
        print('CHECK ACTIVE IDS FROM SCRAPE SPAREPART ACTION: ', active_ids, self.brand, self.source, self.env.context.get('source'))
        sku_vendor_codes = self.env.context.get('sku_vendor_codes')
        sku_vendor_codes = sku_vendor_codes.split(', ') if sku_vendor_codes else []
        source = self.env.context.get('source') or self.source
        ProductTemplate = self.env['product.template']
        products = ProductTemplate.browse(active_ids)
        for prod in products:
            if not self.brand:
                sku_vc_set, prod_vc = set(sku_vendor_codes), set(
                    [sku_rec.product_code for sku_rec in prod.sudo().seller_ids if sku_rec.product_code])
                sku = list(sku_vc_set.intersection(prod_vc))[0] if list(sku_vc_set.intersection(prod_vc)) else ''
            else:
                sku = sku_vendor_codes[0]

            if sku:
                sku_exists = self.env['sku.product.name'].search([('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod.id)])
                if not sku_exists:
                    sku_exists = self.env['sku.product.name'].search([('sku', '=', sku), ('source', '=', source)])
                if sku_exists:
                    active_ids.pop(active_ids.index(prod.id))
                    sku_vendor_codes.pop(sku_vendor_codes.index(sku))
                    return {
                        "type": "ir.actions.act_window",
                        "res_model": "prompt.sku.exists.dialog",
                        "views": [[self.env.ref('grimm_sku.prompt_sku_exists_dialog_form').id, "form"]],
                        "context": {'default_name': sku, 'default_source': source, 'active_ids': active_ids,
                                    'sku_vendor_codes': ', '.join(sku_vendor_codes), 'brand': self.brand, 'active_id': prod.id},
                        "target": "new"
                    }
                else:
                    if not self.all_sources:
                        if source == 'GP':
                            spare_parts = self.fetch_data_gastroparts(sku, prod.id, self.brand)
                            if len(active_ids) == 1 and not spare_parts:
                                raise ValidationError(_(
                                    "Spare part is not available for the SKU '%s'.\nNote: Please make sure that the SKU is present under 'OEM-Teilenummer' or 'Technische Parameter'.\nBesides SKU, please also check for the product brand." % sku))
                        elif source == 'MO':
                            spare_parts = self.fetch_data_mercateo(sku, prod.id, self.brand)
                            if len(active_ids) == 1 and not spare_parts:
                                raise ValidationError(_(
                                    "Spare part is not available for the SKU '%s'.\nNote: Please make sure that the SKU is present under 'Weitere Informationen'.\nBesides SKU, please also check for the product brand." % sku))
                    else:
                        spare_parts_gp = self.fetch_data_gastroparts(sku, prod.id, self.brand)
                        spare_parts_mo = self.fetch_data_mercateo(sku, prod.id, self.brand)
                        if spare_parts_gp:
                            spare_parts = spare_parts_gp
                            source = 'GP'
                        elif spare_parts_mo:
                            spare_parts = spare_parts_mo
                            source = 'MO'
                        else:
                            spare_parts = []

                        if len(active_ids) == 1 and not spare_parts:
                            raise ValidationError(_(
                                "Spare part is not available in any of the sources for the SKU '%s'.\n" % sku))

                    res = self.insert_or_update_sparepart(spare_parts, prod.id)

                    if res:
                        sku_mapping = self.env['sku.mapping'].with_context(
                            {'sku': sku, 'prod_id': prod.id, 'active_ids': active_ids, 'source': source}).action_sku_mapping()
                        if sku_mapping:
                            return sku_mapping

                        sku_attr_prod = self.env['scrape.sparepart.dialog'].with_context(
                            {'active_ids': active_ids}).assign_attributes2product(sku,
                                                                                  self.env[
                                                                                      'product.template'].browse(
                                                                                      prod.id), source)

                        if sku_attr_prod:
                            return sku_attr_prod

    def assign_attributes2product(self, sku, prod, source):
        get_outsource_attributes = self.env['sku.technical.details'].search(
            [('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod.id)])

        if not get_outsource_attributes:
            get_outsource_attributes = self.env['sku.technical.details'].search(
                [('sku', '=', sku), ('source', '=', source)])
        sku_recs = self.env['sku.mapping'].search(
            [('outsourced_attribute', 'in', [os_attr.key for os_attr in get_outsource_attributes]), ('source', '=', source)])
        sku_recs_lst = [str(sku_rec.id) for sku_rec in sku_recs]
        return self.with_context({'active_ids': self.env.context.get('active_ids')}).dialog_attributes2product(sku,
                                                                                                               prod,
                                                                                                               sku_recs,
                                                                                                               sku_recs_lst,
                                                                                                               source)

    def dialog_attributes2product(self, sku, prod, sku_recs, sku_recs_lst, source):
        active_ids = self.env.context.get('active_ids')
        for sku_rec in sku_recs:
            product_name = self.env['sku.product.name'].search([('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod.id)],
                                                               limit=1).name
            if not product_name:
                product_name = self.env['sku.product.name'].search(
                    [('sku', '=', sku), ('source', '=', source)], limit=1).name

            prod.prod_name = product_name if product_name else ''
            attribute_id = sku_rec.partenics_attribute.id

            try:
                if not prod.property_set_id:
                    raise ValidationError(_('Please assign a property set for the product %s' % prod.name))
            except AttributeError:
                raise ValidationError(_('Field property_set_id is not found in the database. shopware_connector module is required to carry out this process.'))

            if attribute_id in [pattr for pattr in prod.property_set_id.product_attribute_ids.ids]:
                if attribute_id not in [attr.attribute_id.id for attr in prod.shopware_property_ids]:
                    val = self.env['sku.technical.details'].search(
                        [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod.id)]).value

                    if not val:
                        val = self.env['sku.technical.details'].search(
                            [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', sku), ('source', '=', source)]).value

                    if val and val not in [val.name for val in sku_rec.partenics_attribute.value_ids]:
                        sku_rec.partenics_attribute.value_ids = [(0, 0, dict(name=val))]

                    val_rec = [aval.id for aval in sku_rec.partenics_attribute.value_ids if aval.name == val]
                    prod.shopware_property_ids = [
                        (0, 0, dict(attribute_id=attribute_id, value_ids=[(6, 0, val_rec)]))]
                else:
                    val = self.env['sku.technical.details'].search(
                        [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', sku), ('source', '=', source), ('product_id', '=', prod.id)]).value

                    if not val:
                        val = self.env['sku.technical.details'].search(
                            [('key', '=', sku_rec.outsourced_attribute), ('sku', '=', sku), ('source', '=', source)]).value

                    if val and val not in [val.name for val in sku_rec.partenics_attribute.value_ids]:
                        sku_rec.partenics_attribute.value_ids = [(0, 0, dict(name=val))]

                    val_rec = [aval.id for aval in sku_rec.partenics_attribute.value_ids if aval.name == val]
                    rec_shop = [attr for attr in prod.shopware_property_ids if attr.attribute_id.id == attribute_id]
                    prod.shopware_property_ids = [
                        (1, rec_shop[0].id, dict(value_ids=[(6, 0, val_rec)]))]

                if str(sku_rec.id) in sku_recs_lst:
                    sku_recs_lst.pop(sku_recs_lst.index(str(sku_rec.id)))

            else:
                if str(sku_rec.id) in sku_recs_lst:
                    sku_recs_lst.pop(sku_recs_lst.index(str(sku_rec.id)))

                return {
                    "type": "ir.actions.act_window",
                    "res_model": "prompt.attribute.exists.dialog",
                    "views": [[self.env.ref('grimm_sku.prompt_attribute_exists_dialog_form').id, "form"]],
                    "context": {'default_product_id': prod.id, 'default_attribute_id': attribute_id,
                                'default_mapping_m2m_char': ','.join(sku_recs_lst), 'default_sku': sku,
                                'default_source_product': product_name, 'active_ids': active_ids,
                                'default_source': source},
                    "target": "new"
                }

            if not active_ids and not sku_recs_lst:
                return self.env['prompt.attribute.exists.dialog'].with_context(
                    {'active_ids': active_ids}).skip_product_action()
