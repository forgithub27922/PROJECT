# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
from bs4 import BeautifulSoup
import base64
import csv
from io import StringIO
import logging
_logger = logging.getLogger(__name__)


class CompareProductPrice(models.TransientModel):
    _name = 'compare.product.price'
    _description = 'Compare Product Prices'

    product_id = fields.Many2one('product.template', string='Connection Type')
    ean_number = fields.Char('EAN Number', related='product_id.ean_number')
    price_info = fields.Html('Price Information', readonly=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cloud_lowest_price = fields.Float("Lowest Price on Cloud")
    cloud_lowest_price_link = fields.Html("Lowest Price on Cloud", readonly=True)

    def google_lookup(self):
        googlePage = requests.get("https://www.google.de/search?q=%s&source=lnms&tbm=shop&sa=X&ved=2ahUKEwiTtLPpgobqAhVOTBoKHaMWDx0Q_AUoAHoECAsQCA&biw=1920&bih=951" % self.ean_number)
        soup = BeautifulSoup(googlePage.content, "html.parser")
        product_link = soup.find_all('a', class_="DKkjqf")
        all_info = []
        for link in product_link:
            href_link = link['href'] #.replace("&","&prds=scoring:pd&",1)
            if 'prds' in href_link:
                split_href = href_link.split("&")
                for index,slice in enumerate(split_href):
                    if 'prds' in slice:
                        split_href[index] = slice + str(",scoring:p")
                href_link = '&'.join(split_href)
            else:
                href_link = href_link.replace("&","&prds=scoring:p&",1)
            productListPage = requests.get("https://www.google.de%s" % href_link)
            listPage = BeautifulSoup(productListPage.content, "html.parser")
            # Sometimes, Google provides wrong results when scraped. When this happens, it is observed that the wrong
            # sources do not have brand information listed.
            # Hence, we check if the brand information exists, it is considered the right source.
            brandDiv = listPage.find_all('div', class_="VOVcm")
            if brandDiv:
                product_table = listPage.find_all('div', id="online")
                childrens = product_table[0].findChildren("div", recursive=False)
                for children in childrens[2:]:
                    details = children.findChildren("div", recursive=True)
                    temp_list = [details[3], details[1].string]
                    anch_tag = temp_list[0].find('a')
                    try:
                        anch_tag['target'] = '_blank'
                    except:
                        raise UserError(
                            _('[406 Invalid response] Google response does not meet our criteria. Please try again!'))
                    if anch_tag.get_text() == 'Grimm Gastrobedarf':
                        continue
                    # if self.calculated_magento_price > float(details[1].string.split('\xa0€')[0].replace('.', '').replace(',', '.')):
                    all_info.append(temp_list)
        return_dict = {}
        if all_info:
            return_dict["success"] = True
            return_dict["data"] = all_info
        else:
            return_dict["success"] = False
            return_dict["data"] = soup
        return return_dict



                #print("Table value is ===> ", children)

            #print("Link is ===> ",product_table)

        #print("Value of SOAP is ===> ", soup)

    @api.model
    def send_cloud_price_email(self, limit=5):
        data = [['ID', 'Article SKU', 'Article Name', 'Our Shop Price', 'Lowest Cloud Price', 'Cloud Link']]
        vals = {'email_from': 'office@grimm-gastrobedarf.de',
                'email_to': self.env["ir.config_parameter"].get_param("cloud.price.alarm.emails"),
                'body_html': "<pre>Liebe Kolleginnen und Kollegen,<br/>"
                             "Das beigefügte Preisblatt finden Sie. Hier finden Sie unseren Shop- und Cloud-Preis.<br/>"
                             "Vielen Dank", 'type': 'email',
                'subject': 'Preis Überwachung: Alarm'}
        mail = self.env['mail.mail'].create(vals)

        query = "select id from product_template where active='t' and id in (select product_tmpl_id from product_product where ean_number is not null and active='t') limit 5"
        self._cr.execute(query)
        product_ids = [i[0] for i in self._cr.fetchall()]
        print("Selected products IDS ==> ", product_ids)
        for prod_id in product_ids:
            product = self.browse(prod_id)
            product._set_lowest_price()
            magento_price = product.calculated_magento_price
            if product.cloud_lowest_price > 0 and magento_price > product.cloud_lowest_price:
                data.append([product.id,product.default_code,product.name,magento_price,product.cloud_lowest_price,product.cloud_lowest_price_link])



        if len(data) > 1:
            f = StringIO()
            csv.writer(f, delimiter=';').writerows(data)
            datas = base64.b64encode(f.getvalue().encode('utf-8'))
            attachment = self.env['ir.attachment'].create(
                {'name': 'cloud_price_alarm', 'type': 'binary', 'datas': datas, 'extension': '.csv',
                 'datas_fname': 'price_alarm.csv'})
            print("Created Attachment is ===> ", attachment)
            mail.attachment_ids = [(4, attachment.id)]

        mail.send()

    def _set_lowest_price(self):
        if self.ean_number:
            price_info = self.google_lookup()
            if price_info.get("success"):
                price_info = price_info.get("data")
                lowest_price = ((price_info[0][1].split("€")[0]).replace(".", "")).replace(",", ".") if price_info else 0
                self.cloud_lowest_price = lowest_price
                self.cloud_lowest_price_link = price_info[0][0] if price_info else ""
        else:
            self.cloud_lowest_price = 0
            self.cloud_lowest_price = ""

    def action_ean_product(self, active_ids=False):
        products = self.browse(active_ids)
        for prod in products:
            if prod.ean_number:
                price_info = prod.google_lookup()
                html_text = ""
                if price_info.get("success"):
                    price_info = price_info.get("data")
                    html_text = "<table class='table'><thead><tr><th scope='col'>#</th><th scope='col'>Source</th><th scope='col'>Price Info</th></tr></thead><tbody>"
                    lowest_price = ((price_info[0][1].split("€")[0]).replace(".","")).replace(",",".") if price_info else 0
                    for index, info in enumerate(price_info):
                        try:
                            class_row = 'alert alert-danger' if prod.calculated_magento_price > float(
                                info[1].split('\xa0€')[0].replace('.', '').replace(',', '.')) else ''
                            html_text += "<tr class='" + class_row + "'><th>" + str(index + 1) + "</th><td>" + str(
                                info[0]) + "</td><td>" + str(info[1]) + "</td></tr>"
                        except:
                            continue
                    html_text += "</tbody></table>"
                    prod.cloud_lowest_price = lowest_price
                else:
                    html_text = price_info.get("data")
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "compare.product.price",
                    "context": {'default_product_id': prod.id, 'default_price_info': html_text},
                    "view_mode": "form",
                    "target": "new"
                }
            else:
                raise UserError(_('EAN number not found!'))
