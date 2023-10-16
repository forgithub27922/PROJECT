# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
from PIL import Image

from datetime import datetime, timedelta
from ebaysdk.exception import ConnectionError
from odoo.addons.sale_ebay.tools.ebaysdk import Trading

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import pycompat
import requests
import json
from bs4 import BeautifulSoup

import logging
_logger = logging.getLogger(__name__)

# eBay api limits ItemRevise calls to 150 per day
MAX_REVISE_CALLS = 150

class EbayProductTemplate(models.Model):
    _name = "ebay.product.template"

    ebay_id = fields.Char('eBay ID', copy=False)
    ebay_backend_id = fields.Many2one('ebay.backend', required=True, copy=False)
    ebay_use = fields.Boolean('Use eBay', default=False)
    ebay_url = fields.Char('eBay url', readonly=True, copy=False)
    ebay_listing_status = fields.Char('eBay Status', default='Unlisted', readonly=True, copy=False)
    ebay_title = fields.Char('Title', size=80,
        help='The title is restricted to 80 characters')
    ebay_subtitle = fields.Char('Subtitle', size=55,
        help='The subtitle is restricted to 55 characters. Fees can be claimed by eBay for this feature')
    ebay_description = fields.Html('eBay Description', default='<p><br></p>')
    ebay_item_condition_id = fields.Many2one('ebay.item.condition', string="Item Condition")
    ebay_category_id = fields.Many2one('ebay.category',
        string="Category", domain=[('category_type', '=', 'ebay'),('leaf_category','=',True)])
    ebay_category_2_id = fields.Many2one('ebay.category',
        string="Category 2 (Optional)", domain=[('category_type', '=', 'ebay'),('leaf_category','=',True)],
        help="The use of a secondary category is not allowed on every eBay sites. Fees can be claimed by eBay for this feature")
    ebay_store_category_id = fields.Many2one('ebay.category',
        string="Store Category (Optional)", domain=[('category_type', '=', 'store'),('leaf_category','=',True)])
    ebay_store_category_2_id = fields.Many2one('ebay.category',
        string="Store Category 2 (Optional)", domain=[('category_type', '=', 'store'),('leaf_category','=',True)])
    ebay_price = fields.Float(string='Starting Price for Auction')
    ebay_buy_it_now_price = fields.Float(string='Buy It Now Price')
    ebay_listing_type = fields.Selection([
        ('Chinese', 'Auction'),
        ('FixedPriceItem', 'Fixed price')], string='Listing Type', default='FixedPriceItem')
    ebay_listing_duration = fields.Selection([
        ('Days_3', '3 Days'),
        ('Days_5', '5 Days'),
        ('Days_7', '7 Days'),
        ('Days_10', '10 Days'),
        ('Days_30', '30 Days (only for fixed price)'),
        ('GTC', 'Good \'Til Cancelled (only for fixed price)')],
        string='Duration', default='GTC')
    ebay_seller_payment_policy_id = fields.Many2one('ebay.policy',
        string="Payment Policy", domain=[('policy_type', '=', 'PAYMENT')])
    ebay_seller_return_policy_id = fields.Many2one('ebay.policy',
        string="Return Policy", domain=[('policy_type', '=', 'RETURN_POLICY')])
    ebay_seller_shipping_policy_id = fields.Many2one('ebay.policy',
        string="Shipping Policy", domain=[('policy_type', '=', 'SHIPPING')])
    ebay_sync_stock = fields.Boolean(string="Use Stock Quantity", default=False)
    ebay_best_offer = fields.Boolean(string="Allow Best Offer", default=False)
    ebay_private_listing = fields.Boolean(string="Private Listing", default=False)
    ebay_start_date = fields.Datetime('Start Date', readonly=1, copy=False)
    ebay_template_id = fields.Many2one('mail.template', string='Description Template',
                                       ondelete='set null',
                                       help='This field contains the template that will be used.')
    name = fields.Char('eBay ID', related='ebay_product_template_id.name', copy=False)
    ebay_product_template_id = fields.Many2one('product.template', string='Product Template',ondelete='set null',)
    ebay_quantity_sold = fields.Integer(related='ebay_product_template_id.product_variant_ids.ebay_quantity_sold', store=True, copy=False)
    ebay_fixed_price = fields.Float(related='ebay_product_template_id.product_variant_ids.ebay_fixed_price', store=True)
    ebay_quantity = fields.Integer("Ebay Quantity")
    product_variant_ids = fields.One2many(comodel_name='product.product', string='Product Variants',
                                   help='Product Variants.', store=False, related='ebay_product_template_id.product_variant_ids',
                                   readonly=True)
    generate_ebay_title = fields.Char(related='ebay_product_template_id.prod_name', string='Generated Ebay title')
    ebay_last_sync = fields.Datetime(string="Last update", copy=False)

    calculated_ebay_price = fields.Float(string='Ebay Price', help='Calculated Sale Price (for Ebay)',
                                            compute='_compute_ebay_price')
    product_variant_count = fields.Integer('Variant Count', related='ebay_product_template_id.product_variant_count')

    _sql_constraints = [('template_id_backend_id_unique', 'unique (ebay_product_template_id,ebay_backend_id)',
                         _('You can assign an ebay backend for same product only once!'))]

    img_link_simple = fields.Char(string="Simple Image Link", compute='_compute_image_link_simple')
    img_link_360 = fields.Char(string="360 Image Link", compute='_compute_image_link_360')

    def write(self, vals):
        res = super(EbayProductTemplate, self).write(vals)
        for rec in self:
            active_record = rec.ebay_product_template_id.ebay_product_ids.filtered(lambda r: r.ebay_listing_status == "Active")
            rec.ebay_product_template_id.ebay_listing_status = "listed" if active_record else "unlisted"
        return res

    def unlink(self):
        template_ids = []
        for rec in self:
            template_ids.append(rec.ebay_product_template_id)
        res = super(EbayProductTemplate, self).unlink()
        for rec in template_ids:
            active_record = rec.ebay_product_ids.filtered(
                lambda r: r.ebay_listing_status == "Active")
            rec.ebay_listing_status = "listed" if active_record else "unlisted"
        return res

    @api.depends('ebay_product_template_id')
    def _compute_image_link_simple(self):
        for record in self:
            if record.ebay_product_template_id.barcode:
                req = requests.get("https://imageserver.partenics.de/odoo/%s?format=json" % self.ebay_product_template_id.barcode)
                if req.status_code == 200:
                    response = json.loads(req.content.decode("utf-8"))
                    image_link = False
                    for server_image in response.get("images", []):
                        if server_image.get("type", "") == "image":
                            if not image_link:
                                image_link = True
                                record.img_link_simple = server_image.get("srcUrl", False)

    @api.depends('ebay_product_template_id')
    def _compute_image_link_360(self):
        for record in self:
            if record.ebay_product_template_id.barcode:
                req = requests.get(
                    "https://imageserver.partenics.de/odoo/%s?format=json" % self.ebay_product_template_id.barcode)
                if req.status_code == 200:
                    response = json.loads(req.content.decode("utf-8"))
                    image_link = False
                    for server_image in response.get("images", []):
                        if server_image.get("type", "") == "360":
                            if not image_link:
                                image_link = True
                                record.img_link_360 = server_image.get("previewUrl", False)

    def tracking_ebay_price(self):
        self.ensure_one()
        if len(self.product_variant_ids) == 1:
            return self.product_variant_ids[0].tracking_ebay_price()
        raise Warning(
            'Product Template hat multiple Product Variants. Please tracking the price calculation on the Product Variant')

    @api.model
    def _cron_sync_ebay_products(self, sync_big_stocks=False, auto_commit=False):
        self.sync_product_status(sync_big_stocks=sync_big_stocks, auto_commit=auto_commit)

    @api.model
    def sync_product_status(self, sync_big_stocks=False, auto_commit=False):
        self._sync_recent_product_status(1, sync_big_stocks=sync_big_stocks, auto_commit=auto_commit)
        self._sync_old_product_status(sync_big_stocks=sync_big_stocks, auto_commit=auto_commit)

    @api.onchange('ebay_template_id')
    def onchange_ebay_template_id(self):
        if self.ebay_template_id:
            self.ebay_description = self.ebay_template_id.render_template(self.ebay_template_id.body_html,'ebay.product.template', self._origin.id)

    @api.onchange('ebay_backend_id')
    def onchange_ebay_backend_id(self):
        if self.ebay_backend_id and self._context.get("parent_model","") == "product.template":
            prod_data = self.env["product.template"].browse(int(self._context.get("parent_id")))
            if prod_data:
                self.ebay_title = prod_data.prod_name if prod_data.prod_name else prod_data.name
                index = 1
                for categ in prod_data.shopware_categories:
                    mapping = self.env['ebay.mapping'].search([
                        ('ebay_backend_id', '=', self.ebay_backend_id.id),
                        ('shop_categ_id', '=', categ.id),
                        ('mapping_type', '=', 'category'),
                    ], limit=1)
                    if mapping and index == 1:
                        self.ebay_category_id = mapping.ebay_categ_id.id
                        index = 2
                    elif mapping and index == 2:
                        self.ebay_category_2_id = mapping.ebay_categ_id.id
                        index = 3
            if prod_data.property_set_id:
                mapping = self.env['ebay.mapping'].search([
                    ('ebay_backend_id', '=', self.ebay_backend_id.id),
                    ('property_id', '=', prod_data.property_set_id.id),
                    ('mapping_type', '=', 'property'),
                ], limit=1)
                if mapping:
                    self.ebay_store_category_id = mapping.ebay_store_categ_id.id

    def _create_picture_url(self):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.ebay_product_template_id.id),
            ('mimetype', 'ilike', 'image'),
        ], order="create_date")

        urls = []
        #Below for loop will submit data from image tabs.
        for all_image in self.ebay_product_template_id.image_ids.filtered(lambda rec: rec.transfer_to_ebay == True):
            imgdata = base64.b64decode(all_image.manual_image_data)
            im = Image.open(io.BytesIO(imgdata))
            width, height = im.size
            if width >= 500 or height >= 500:
                image = io.BytesIO(base64.standard_b64decode(all_image.manual_image_data))
                files = {'file': ('EbayImage', image)}
                pictureData = {
                    "WarningLevel": "High",
                    "PictureName": self.ebay_product_template_id.barcode if self.ebay_product_template_id.barcode else self.ebay_product_template_id.default_code
                }
                response = self.ebay_execute('UploadSiteHostedPictures', pictureData, files=files)
                urls.append(response.dict()['SiteHostedPictureDetails']['FullURL'])

        for shop_image in self.ebay_product_template_id.shopware_image_ids.filtered(lambda rec: rec.file_select == 'upload'):
            imgdata = base64.b64decode(shop_image.image)
            im = Image.open(io.BytesIO(imgdata))
            width, height = im.size
            if width >= 500 or height >= 500:
                image = io.BytesIO(base64.standard_b64decode(shop_image.image))
                files = {'file': ('EbayImage', image)}
                pictureData = {
                    "WarningLevel": "High",
                    "PictureName": self.ebay_product_template_id.barcode if self.ebay_product_template_id.barcode else self.ebay_product_template_id.default_code
                }
                response = self.ebay_execute('UploadSiteHostedPictures', pictureData, files=files)
                urls.append(response.dict()['SiteHostedPictureDetails']['FullURL'])


        if self.ebay_product_template_id.is_image_on_server:
            try:
                if self.ebay_product_template_id.barcode:
                    req=requests.get("https://imageserver.partenics.de/odoo/%s?format=json"%self.ebay_product_template_id.barcode)
                    #req = requests.get("https://imageserver.partenics.de/odoo/00213729?format=json")
                    if req.status_code == 200:
                        response = json.loads(req.content.decode("utf-8"))

                        for server_image in response.get("images",[]):
                            if server_image.get("type","") == "image":
                                img_url = server_image.get("srcUrl", False)
                                _logger.info("......................................IMAGE URL IS =======> %s"%img_url)
                                img_req = requests.get(img_url)
                                #if img_url:
                                #    #data = base64.b64encode(img_req.contents)
                                imgdata = base64.b64encode(img_req.content)
                                image = io.BytesIO(base64.standard_b64decode(imgdata))
                                files = {'file': ('EbayImage', image)}
                                pictureData = {
                                    "WarningLevel": "High",
                                    "PictureName": self.ebay_product_template_id.barcode if self.ebay_product_template_id.barcode else self.ebay_product_template_id.default_code
                                }
                                response = self.ebay_execute('UploadSiteHostedPictures', pictureData, files=files)
                                urls.append(response.dict()['SiteHostedPictureDetails']['FullURL'])
            except:
                pass

        return urls

    def _prepare_item_dict(self):
        if self.ebay_sync_stock:
            self.ebay_quantity = max(int(self.ebay_product_template_id.virtual_available), 0)
        country_id = self.ebay_backend_id.get_values()["ebay_country"]
        country = self.env['res.country'].browse(int(country_id))
        currency_id = self.ebay_backend_id.get_values()["ebay_currency"]
        currency = self.env['res.currency'].browse(int(currency_id))
        comp_currency = self.env.user.company_id.currency_id
        item = {
            "Item": {
                "Title": self.ebay_product_template_id._ebay_encode(self.ebay_title),
                "PrimaryCategory": {"CategoryID": self.ebay_category_id.category_id},
                "StartPrice": comp_currency.compute(self.calculated_ebay_price, currency)
                if self.ebay_listing_type == 'FixedPriceItem'
                else comp_currency.compute(self.ebay_fixed_price, currency),
                "CategoryMappingAllowed": "true",
                "Country": country.code,
                "Currency": currency.name,
                "ConditionID": self.ebay_item_condition_id.code,
                "ListingDuration": self.ebay_listing_duration,
                "ListingType": self.ebay_listing_type,
                "PostalCode": self.ebay_backend_id.get_values()["ebay_zip_code"],
                "Location": self.ebay_backend_id.get_values()["ebay_location"],
                "Quantity": self.ebay_quantity,
                "BestOfferDetails": {'BestOfferEnabled': self.ebay_best_offer},
                "PrivateListing": self.ebay_private_listing,
                "SellerProfiles": {
                    "SellerPaymentProfile": {
                        "PaymentProfileID": self.ebay_seller_payment_policy_id.policy_id,
                    },
                    "SellerReturnProfile": {
                        "ReturnProfileID": self.ebay_seller_return_policy_id.policy_id,
                    },
                    "SellerShippingProfile": {
                        "ShippingProfileID": self.ebay_seller_shipping_policy_id.policy_id,
                    }
                },
            }
        }
        if self.ebay_description:# and self.ebay_template_id:
            #description = self.ebay_template_id.render_template(self.ebay_template_id.body_html, 'ebay.product.template',self.id)
            html_text = self.ebay_description
            soup = BeautifulSoup(html_text, 'html.parser')
            value_text = soup.find_all('strong', class_="grimm")
            value_text[0].string = str(value_text[0].string).replace("<","&lt;")
            value_text[0].string = str(value_text[0].string).replace(">", "&gt;")
            item['Item']['Description'] = '<![CDATA[' + soup + ']]>'
        if self.ebay_subtitle:
            item['Item']['SubTitle'] = self.ebay_product_template_id._ebay_encode(self.ebay_subtitle)
        picture_urls = self._create_picture_url()
        if picture_urls:
            item['Item']['PictureDetails'] = {'PictureURL': picture_urls}
            if self.ebay_backend_id.get_values()["ebay_gallery_plus"]:
                item['Item']['PictureDetails']['GalleryType'] = 'Plus'
        if self.ebay_listing_type == 'Chinese' and self.ebay_buy_it_now_price:
            item['Item']['BuyItNowPrice'] = comp_currency.compute(self.ebay_buy_it_now_price, currency)
        NameValueList = []
        variant = self.product_variant_ids.filtered('ebay_use')
        # We set by default the brand and the MPN because of the new eBay policy
        # That make them mandatory in most category
        default_code = self.ebay_product_template_id.default_code.split("-", 1)
        if len(default_code) > 1:
            default_code = default_code[1]
        item['Item']['ProductListingDetails'] = {'BrandMPN': {'Brand': self.ebay_product_template_id.product_brand_id.name if self.ebay_product_template_id.product_brand_id else 'Markenlos/No-Name'}}
        item['Item']['ProductListingDetails']['BrandMPN']['MPN'] = 'Nicht zutreffend' if self.ebay_product_template_id.default_code.upper().startswith("GEV-") else default_code
        item['Item']['ProductListingDetails']['EAN'] = self.ebay_product_template_id.ean_number if self.ebay_product_template_id.ean_number else 'Nicht zutreffend'

        # If only one variant selected to be published, we don't create variant
        # but set the variant's value has an item specific on eBay
        if len(variant) == 1 \
                and self.ebay_listing_type == 'FixedPriceItem':
            if self.ebay_sync_stock:
                variant.ebay_quantity = max(int(variant.virtual_available), 0)
            item['Item']['Quantity'] = self.ebay_quantity
            item['Item']['StartPrice'] = variant.calculated_ebay_price
        # We use the attribute to set the attributes linked to computed shipping policies
        # We don't use attributes since this fix has been done in stable release but will be done
        # in master.
        # We don't use the weight attribute due to the fact that eBay handles the English system
        # of measurement which uses Lbs and Oz. Then we cannot just split the weight field.
        ShippingPackageAttributes = [
            'PackageDepth', 'PackageLength', 'PackageWidth', 'WeightMajor',
            'WeightMinor', 'ShippingIrregular', 'ShippingPackage'
        ]
        # If one attribute has only one value, we don't create variant
        # but set the value has an item specific on eBay
        if self.ebay_product_template_id.attribute_line_ids:
            for attribute in self.ebay_gallery_plus.attribute_line_ids:
                if len(attribute.value_ids) == 1:
                    attr_name = attribute.attribute_id.name
                    attr_value = self.ebay_product_template_id._ebay_encode(attribute.value_ids.name)
                    # We used the attributes in Odoo to match the Brand and MPN attributes
                    # But since 1st March 2016, eBay separated them from the other attributes
                    if attr_name == 'Brand':
                        item['Item']['ProductListingDetails']['BrandMPN']['Brand'] = attr_value
                    elif attr_name == 'MPN':
                        item['Item']['ProductListingDetails']['BrandMPN']['MPN'] = attr_value
                    elif attr_name in ShippingPackageAttributes:
                        if 'ShippingPackageDetails' not in item['Item']:
                            item['Item']['ShippingPackageDetails'] = {}
                        item['Item']['ShippingPackageDetails'][self.ebay_product_template_id._ebay_encode(attr_name)] = attr_value
                    else:
                        NameValueList.append({
                            'Name': self.ebay_product_template_id._ebay_encode(attr_name),
                            'Value': attr_value,
                        })

        # We add the Brand and the MPN at the end of the loop
        # because these attributes are mandatory since 1st March 2016
        # but some eBay site are not taking into account the ProductListingDetails.
        # This avoid to loop in the NameValueList array to ensure that it contains
        # Brand and MPN attributes
        brand_mpn = [
            {'Name': 'Marke',
             'Value': item['Item']['ProductListingDetails']['BrandMPN']['Brand']},
            {'Name': 'Herstellernummer',
             'Value': item['Item']['ProductListingDetails']['BrandMPN']['MPN']},
            {'Name': 'EAN',
             'Value': item['Item']['ProductListingDetails']['EAN']}
        ]
        NameValueList += brand_mpn
        tech_attribute = []
        for property in self.ebay_product_template_id.shopware_property_ids:
            if property.attribute_id.id != 878:  # Added related to OD-941
                temp_dict = {}
                temp_dict["Name"] = property.attribute_id.name
                temp_dict["Value"] = ", ".join([val.name for val in property.value_ids])
                tech_attribute.append(temp_dict)

        NameValueList += tech_attribute

        if NameValueList:
            item['Item']['ItemSpecifics'] = {'NameValueList': NameValueList}
        if self.ebay_category_2_id:
            item['Item']['SecondaryCategory'] = {'CategoryID': self.ebay_category_2_id.category_id}
        if self.ebay_store_category_id:
            item['Item']['Storefront'] = {
                'StoreCategoryID': self.ebay_store_category_id.category_id,
                'StoreCategoryName': self.ebay_product_template_id._ebay_encode(self.ebay_store_category_id.name),
            }
            if self.ebay_store_category_2_id:
                item['Item']['Storefront']['StoreCategory2ID'] = self.ebay_store_category_2_id.category_id
                item['Item']['Storefront']['StoreCategory2Name'] = self.ebay_product_template_id._ebay_encode(self.ebay_store_category_2_id.name)
        return item

    def _prepare_variant_dict(self):
        if not self.ebay_product_template_id.product_variant_ids.filtered('ebay_use'):
            raise UserError(_("Error Encountered.\n No Variant Set To Be Listed On eBay."))
        currency_id = self.ebay_backend_id.get_values()["ebay_currency"]
        currency = self.env['res.currency'].browse(int(currency_id))
        comp_currency = self.env.user.company_id.currency_id
        items = self._prepare_item_dict()
        items['Item']['Variations'] = {'Variation': []}
        variations = items['Item']['Variations']['Variation']

        name_values = {}
        for variant in self.product_variant_ids:
            if self.ebay_sync_stock:
                variant.ebay_quantity = max(int(variant.virtual_available), 0)
            if variant.ebay_use and not variant.ebay_quantity and \
                    not self.ebay_backend_id.get_values()["ebay_out_of_stock"]:
                raise UserError(
                    _('All the quantities must be greater than 0 or you need to enable the Out Of Stock option.'))
            variant_name_values = []
            for spec in variant.attribute_value_ids:
                attr_line = self.attribute_line_ids.filtered(
                    lambda l: l.attribute_id.id == spec.attribute_id.id)
                if len(attr_line.value_ids) > 1:
                    if spec.attribute_id.name not in name_values:
                        name_values[spec.attribute_id.name] = []
                    if spec not in name_values[spec.attribute_id.name]:
                        name_values[spec.attribute_id.name].append(spec)
                    variant_name_values.append({
                        'Name': self._ebay_encode(spec.attribute_id.name),
                        'Value': self._ebay_encode(spec.name),
                    })
            # Since 1st March 2016, identifiers are mandatory
            # We set default values in case none is set by the user
            # Check the length of the barcode field to guess its type.
            upc = 'Nicht zutreffend'
            ean = 'Nicht zutreffend'
            if variant.barcode:
                if len(variant.barcode) == 12 and self.check_encoding(variant.barcode, 'upc'):
                    upc = variant.barcode
                elif len(variant.barcode) == 13 and self.check_encoding(variant.barcode, 'ean13'):
                    ean = variant.barcode
            variations.append({
                'Quantity': variant.ebay_quantity,
                'StartPrice': comp_currency.compute(variant.ebay_fixed_price, currency),
                'VariationSpecifics': {'NameValueList': variant_name_values},
                'Delete': False if variant.ebay_use else True,
                'VariationProductListingDetails': {
                    'UPC': upc,
                    'EAN': ean}
            })
        # example of a valid name value list array
        # possible_name_values = [{'Name':'size','Value':['16gb','32gb']},{'Name':'color', 'Value':['red','blue']}]
        possible_name_values = []
        for key in name_values:
            possible_name_values.append({
                'Name': self._ebay_encode(key),
                'Value': [self._ebay_encode(n.name) for n in sorted(name_values[key], key=lambda v: v.sequence)]
            })
        items['Item']['Variations']['VariationSpecificsSet'] = {
            'NameValueList': possible_name_values
        }
        return items

    def _prepare_non_variant_dict(self):
        item = self._prepare_item_dict()
        # Set default value to UPC
        item['Item']['ProductListingDetails']['UPC'] = 'Nicht zutreffend'
        # Check the length of the barcode field to guess its type.

        if self.ebay_product_template_id.barcode:
            if len(self.ebay_product_template_id) == 12 and self.ebay_product_template_id.check_encoding(self.barcode, 'upc'):
                item['Item']['ProductListingDetails']['UPC'] = self.ebay_product_template_id.barcode
            elif len(self.ebay_product_template_id) == 13 and self.ebay_product_template_id.check_encoding(self.barcode, 'ean13'):
                item['Item']['ProductListingDetails']['EAN'] = self.ebay_product_template_id.barcode
        return item

    def _get_item_dict(self):
        if len(self.ebay_product_template_id.product_variant_ids) > 1 \
                and self.ebay_listing_type == 'FixedPriceItem':
            item_dict = self._prepare_variant_dict()
        else:
            item_dict = self._prepare_non_variant_dict()
        return item_dict

    @api.model
    def get_ebay_api(self, domain, backend_id=False):
        ebay_api = self.ebay_backend_id
        if not ebay_api:
            ebay_api = backend_id
            if not ebay_api:
                raise UserError("Please configure Ebay backend for " + str(self.user.company_id.name))
        dev_id = ebay_api.ebay_dev_id
        site_id = ebay_api.ebay_site
        site = self.env['ebay.site'].browse(int(site_id))
        if domain == 'sand':
            app_id = ebay_api.ebay_sandbox_app_id
            cert_id = ebay_api.ebay_sandbox_cert_id
            token = ebay_api.ebay_sandbox_token
            domain = 'api.sandbox.ebay.com'
        else:
            app_id = ebay_api.ebay_prod_app_id
            cert_id = ebay_api.ebay_prod_cert_id
            token = ebay_api.ebay_prod_token
            domain = 'api.ebay.com'

        if not app_id or not cert_id or not token:
            action = self.env.ref('sale.action_sale_config_settings')
            raise RedirectWarning(_('One parameter is missing.'),
                                  action.id, _('Configure The eBay Integrator Now'))

        return Trading(domain=domain,
                       config_file=None,
                       appid=app_id,
                       devid=dev_id,
                       certid=cert_id,
                       token=token,
                       siteid=site.ebay_id)

    @api.model
    def ebay_execute(self, verb, data=None, list_nodes=[], verb_attrs=None, files=None, backend_id=False):
        ebay_backend_id = self.ebay_backend_id
        if not self.ebay_backend_id:
            ebay_backend_id = backend_id
            if not ebay_backend_id:
                raise UserError("Please configure Ebay backend for " + str(self.env.user.company_id.name))
        domain = ebay_backend_id.get_values()["ebay_domain"]
        ebay_api = self.get_ebay_api(domain, backend_id=backend_id)
        try:
            return ebay_api.execute(verb, data, list_nodes, verb_attrs, files)
        except ConnectionError as e:
            errors = e.response.dict()['Errors']
            if not isinstance(errors, list):
                errors = [errors]
            error_message = ''
            for error in errors:
                if error['SeverityCode'] == 'Error':
                    error_message += error['LongMessage'] + '(' + error['ErrorCode'] + ')'
            if error['ErrorCode'] == '21916884':
                error_message += _('Or the condition is not compatible with the category.')
            if error['ErrorCode'] == '10007' or error['ErrorCode'] == '21916803':
                error_message = _('eBay is unreachable. Please try again later.')
            if error['ErrorCode'] == '21916635':
                error_message = _(
                    'Impossible to revise a listing into a multi-variations listing.\n Create a new listing.')
            if error['ErrorCode'] == '942':
                error_message += _(" If you want to set quantity to 0, the Out Of Stock option should be enabled"
                                   " and the listing duration should set to Good 'Til Canceled")
            if error['ErrorCode'] == '21916626':
                error_message = _(" You need to have at least 2 variations selected for a multi-variations listing.\n"
                                  " Or if you try to delete a variation, you cannot do it by unselecting it."
                                  " Setting the quantity to 0 is the safest method to make a variation unavailable.")
            raise UserError(_("Error Encountered.\n'%s'") % (error_message,))

    def push_product_ebay(self):
        if self.ebay_listing_status != 'Active':
            item_dict = self._get_item_dict()

            response = self.ebay_execute('AddItem' if self.ebay_listing_type == 'Chinese'
                                         else 'AddFixedPriceItem', item_dict, backend_id=self.ebay_backend_id)
            print("Return response from ebay is ===> ", response)
            self._set_variant_url(response.dict()['ItemID'])
            self._update_ebay_data(response.dict())

    def relist_product_ebay(self):
        item_dict = self._get_item_dict()
        # set the item id to relist the correct ebay listing
        item_dict['Item']['ItemID'] = self.ebay_id
        response = self.ebay_execute('RelistItem' if self.ebay_listing_type == 'Chinese'
                                     else 'RelistFixedPriceItem', item_dict, backend_id=self.ebay_backend_id)
        self._set_variant_url(response.dict()['ItemID'])
        self._update_ebay_data(response.dict())

    def revise_product_ebay(self):
        item_dict = self._get_item_dict()
        # set the item id to revise the correct ebay listing
        item_dict['Item']['ItemID'] = self.ebay_id
        if not self.ebay_subtitle:
            item_dict['DeletedField'] = 'Item.SubTitle'

        response = self.ebay_execute('ReviseItem' if self.ebay_listing_type == 'Chinese'
                                     else 'ReviseFixedPriceItem', item_dict, backend_id=self.ebay_backend_id)
        self._set_variant_url(response.dict()['ItemID'])
        self._update_ebay_data(response.dict())

    def end_listing_product_ebay(self):
        call_data = {"ItemID": self.ebay_id,
                     "EndingReason": "NotAvailable"}
        self.ebay_execute('EndItem' if self.ebay_listing_type == 'Chinese'
                          else 'EndFixedPriceItem', call_data, backend_id=self.ebay_backend_id)
        self.ebay_listing_status = 'Ended'

    def _update_ebay_data(self, response):
        domain = self.ebay_backend_id.get_values()["ebay_domain"]
        item = self.ebay_execute('GetItem', {'ItemID': response['ItemID']}, backend_id=self.ebay_backend_id).dict()
        qty = int(item['Item']['Quantity']) - int(item['Item']['SellingStatus']['QuantitySold'])
        self.write({
            'ebay_listing_status': 'Active' if qty > 0 else 'Out Of Stock',
            'ebay_id': response['ItemID'],
            'ebay_url': item['Item']['ListingDetails']['ViewItemURL'],
            'ebay_start_date': datetime.strptime(response['StartTime'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        })

    @api.model
    def _sync_recent_product_status(self, page_number=1, sync_big_stocks=False, auto_commit=False):
        call_data = {'StartTimeFrom': str(datetime.today() - timedelta(days=119)),
                     'StartTimeTo': str(datetime.today()),
                     'DetailLevel': 'ReturnAll',
                     'Pagination': {'EntriesPerPage': 200,
                                    'PageNumber': page_number,
                                    }
                     }
        try:
            response = self.ebay_execute('GetSellerList', call_data, backend_id=self.ebay_backend_id)
        except UserError as e:
            if auto_commit:
                self.env.cr.rollback()
                # self.env.user.message_post( #Odoo13Change
                #     body=_("eBay error: Impossible to synchronize the products. \n'%s'") % e.args[0])
                self.env.cr.commit()
                return
            else:
                raise e
        except RedirectWarning as e:
            if not auto_commit:
                raise e
            # not configured, ignore
            return
        if response.dict()['ItemArray'] is None:
            return
        items = response.dict()['ItemArray']['Item']
        if not isinstance(items, list):
            items = [items]
        for item in items:
            domain = [
                ('ebay_id', '=', item['ItemID']),
                ('ebay_product_template_id.virtual_available', '>' if sync_big_stocks else '<', MAX_REVISE_CALLS),
                ('ebay_use', '=', True),
            ]
            product = self.search(domain)
            if product:
                product._sync_transaction(item, auto_commit=auto_commit)
        if page_number < int(response.dict()['PaginationResult']['TotalNumberOfPages']):
            self._sync_recent_product_status(page_number + 1)

    @api.model
    def _sync_old_product_status(self, sync_big_stocks=False, auto_commit=False):
        date = (datetime.today() - timedelta(days=119)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        domain = [
            ('ebay_use', '=', True),
            ('ebay_start_date', '<', date),
            ('ebay_listing_status', 'in', ['Active', 'Error']),
            ('ebay_product_template_id.virtual_available', '>' if sync_big_stocks else '<', MAX_REVISE_CALLS),
        ]
        products = self.search(domain)
        for product in products:
            response = self.ebay_execute('GetItem', {'ItemID': product.ebay_id}, backend_id=self.ebay_backend_id)
            product.ebay_product_template_id._sync_transaction(response.dict()['Item'], auto_commit=auto_commit)
        return

    def sync_available_qty(self):
        if self.ebay_sync_stock:
            if self.ebay_listing_status in ['Active', 'Error']:
                # The product is Active on eBay but there is no more stock
                if self.ebay_product_template_id.virtual_available <= 0:
                    # Only revise product if there is a change of quantity
                    if len(self.product_variant_ids.filtered('ebay_use')) > 1:
                        for variant in self.product_variant_ids:
                            if variant.virtual_available != variant.ebay_quantity:
                                # If the Out Of Stock option is enabled only need to revise the quantity
                                if self.ebay_backend_id.get_values()["ebay_out_of_stock"]:
                                    self.revise_product_ebay()
                                    self.ebay_listing_status = 'Out Of Stock'
                                else:
                                    self.end_listing_product_ebay()
                                    self.ebay_listing_status = 'Ended'
                    elif self.ebay_quantity != self.ebay_product_template_id.virtual_available:
                        # If the Out Of Stock option is enabled only need to revise the quantity
                        if self.ebay_backend_id.get_values()["ebay_out_of_stock"]:
                            self.revise_product_ebay()
                            self.ebay_listing_status = 'Out Of Stock'
                        else:
                            self.end_listing_product_ebay()
                            self.ebay_listing_status = 'Ended'
                # The product is Active on eBay and there is some stock
                # Check if the quantity in Odoo is different than the one on eBay
                # If it is the case revise the quantity
                else:
                    if len(self.product_variant_ids.filtered('ebay_use')) > 1:
                        for variant in self.product_variant_ids:
                            if variant.virtual_available != variant.ebay_quantity:
                                self.revise_product_ebay()
                                break
                    else:
                        if self.ebay_quantity != self.ebay_product_template_id.virtual_available:
                            self.revise_product_ebay()
            elif self.ebay_listing_status == 'Out Of Stock':
                # The product is Out Of Stock on eBay but there is stock in Odoo
                # If the Out Of Stock option is enabled then only revise the product
                if self.ebay_product_template_id.virtual_available > 0 and self.ebay_quantity != self.ebay_product_template_id.virtual_available:
                    if self.env['ir.config_parameter'].sudo().get_param('ebay_out_of_stock'):
                        self.revise_product_ebay()
                    else:
                        self.relist_product_ebay()

    def _sync_transaction(self, item, auto_commit=False):
        try:
            if self.ebay_listing_status != 'Ended' \
                    and self.ebay_listing_status != 'Out Of Stock':
                self.ebay_listing_status = item['SellingStatus']['ListingStatus']
                if self.ebay_backend_id.get_values()["ebay_out_of_stock"] and \
                        self.ebay_listing_status == 'Ended':
                    self.ebay_listing_status = 'Out Of Stock'
                if int(item['SellingStatus']['QuantitySold']) > 0:
                    call_data = {
                        'ItemID': item['ItemID'],
                    }
                    if self.ebay_last_sync:
                        call_data['ModTimeFrom'] = str(self.ebay_last_sync)
                        self.ebay_last_sync = datetime.now()
                    resp = self.ebay_execute('GetItemTransactions', call_data, backend_id=self.ebay_backend_id).dict()
                    if 'TransactionArray' in resp:
                        transactions = resp['TransactionArray']['Transaction']
                        if not isinstance(transactions, list):
                            transactions = [transactions]
                        for transaction in transactions:
                            if transaction['Status']['CheckoutStatus'] == 'CheckoutComplete':
                                self.create_sale_order(transaction)
            self.sync_available_qty()
            self.env.cr.commit()
        except UserError as e:
            if auto_commit:
                self.env.cr.rollback()
                self.ebay_listing_status = 'Error'
                self.message_post(
                    body=_("eBay error: Impossible to synchronize the products. \n'%s'") % e.args[0])
                self.env.cr.commit()
            else:
                raise e
        except RedirectWarning as e:
            if not auto_commit:
                raise e
            # not configured, ignore
            return

    def create_sale_order(self, transaction):
        if not self.env['sale.order'].search([
            ('client_order_ref', '=', transaction['OrderLineItemID'])]):
            # After 15 days eBay doesn't send the email anymore but 'Invalid Request'.
            # If 2 transactions are synchronized with 2 different buyers with 'Invalid Request',
            # the second buyer information will override the firs one. So we make the search
            # on the ebay_id instead.
            email = transaction['Buyer']['Email']
            if email == "Invalid Request":
                email = False
                partner = self.env['res.partner'].search([
                    ('ebay_id', '=', transaction['Buyer']['UserID'])])
            else:
                partner = self.env['res.partner'].search([
                    ('email', '=', email)])
            if not partner:
                partner = self.env['res.partner'].create({'name': transaction['Buyer']['UserID']})
            if len(partner) > 1:
                partner = partner[0]
            partner_data = {
                'name': transaction['Buyer']['UserID'],
                'ebay_id': transaction['Buyer']['UserID'],
                'email': email,
                'ref': 'eBay',
            }
            # if we reuse an existing partner, addresses might already been set on it
            # so we hold the address data in a temporary dictionary to see if we need to create it or not
            shipping_data = {}
            if 'BuyerInfo' in transaction['Buyer'] and \
                    'ShippingAddress' in transaction['Buyer']['BuyerInfo']:
                infos = transaction['Buyer']['BuyerInfo']['ShippingAddress']
                partner_data['name'] = infos.get('Name')
                shipping_data['name'] = infos.get('Name')
                shipping_data['street'] = infos.get('Street1')
                shipping_data['street2'] = infos.get('Street2')
                shipping_data['city'] = infos.get('CityName')
                shipping_data['zip'] = infos.get('PostalCode')
                shipping_data['phone'] = infos.get('Phone')
                shipping_data['country_id'] = self.env['res.country'].search([
                    ('code', '=', infos['Country'])
                ]).id
                state = self.env['res.country.state'].search([
                    ('code', '=', infos.get('StateOrProvince')),
                    ('country_id', '=', shipping_data['country_id'])
                ])
                if not state:
                    state = self.env['res.country.state'].search([
                        ('name', '=', infos.get('StateOrProvince')),
                        ('country_id', '=', shipping_data['country_id'])
                    ])
                shipping_data['state_id'] = state.id
            shipping_partner = partner._find_existing_address(shipping_data)
            if not shipping_partner:
                # if the partner already has an address we create a new child contact to hold it
                # otherwise we can directly set the new address on the partner
                if partner.street:
                    contact_data = {'parent_id': partner.id, 'type': 'delivery'}
                    shipping_partner = self.env['res.partner'].create({**shipping_data, **contact_data})
                else:
                    partner.write(shipping_data)
                    shipping_partner = partner

            partner.write(partner_data)
            fp_id = self.env['account.fiscal.position'].get_fiscal_position(partner.id)
            if fp_id:
                partner.property_account_position_id = fp_id
            if self.product_variant_count > 1:
                if 'Variation' in transaction:
                    variant = self.product_variant_ids.filtered(
                        lambda l:
                        l.ebay_use and
                        l.ebay_variant_url.split("vti", 1)[1] ==
                        transaction['Variation']['VariationViewItemURL'].split("vti", 1)[1])
                # If multiple variants but only one listed on eBay as Item Specific
                else:
                    call_data = {'ItemID': self.ebay_id, 'IncludeItemSpecifics': True}
                    resp = self.ebay_execute('GetItem', call_data, backend_id=self.ebay_backend_id)
                    name_value_list = resp.dict()['Item']['ItemSpecifics']['NameValueList']
                    if not isinstance(name_value_list, list):
                        name_value_list = [name_value_list]
                    # get only the item specific in the value list
                    attrs = []
                    # get the attribute.value ids in order to get the variant listed on ebay
                    for spec in (n for n in name_value_list if n['Source'] == 'ItemSpecific'):
                        attr = self.env['product.attribute.value'].search(
                            [('name', '=', spec['Value'])])
                        attrs.append(('attribute_value_ids', '=', attr.id))
                    variant = self.env['product.product'].search(attrs).filtered(
                        lambda l: l.product_tmpl_id.id == self.id)
            else:
                variant = self.product_variant_ids[0]
            variant.ebay_quantity_sold = variant.ebay_quantity_sold + int(transaction['QuantityPurchased'])
            if not self.ebay_sync_stock:
                variant.ebay_quantity = variant.ebay_quantity - int(transaction['QuantityPurchased'])
                variant_qty = 0
                if len(self.product_variant_ids.filtered('ebay_use')) > 1:
                    for variant in self.product_variant_ids:
                        variant_qty += variant.ebay_quantity
                else:
                    variant_qty = variant.ebay_quantity
                if variant_qty <= 0:
                    if self.env['ir.config_parameter'].sudo().get_param('ebay_out_of_stock'):
                        self.ebay_listing_status = 'Out Of Stock'
                    else:
                        self.ebay_listing_status = 'Ended'
            sale_order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'partner_shipping_id': shipping_partner.id,
                'state': 'draft',
                'client_order_ref': transaction['OrderLineItemID'],
                'origin': 'eBay' + transaction['TransactionID'],
                'fiscal_position_id': fp_id if fp_id else False,
            })
            if self.env['ir.config_parameter'].sudo().get_param('ebay_sales_team'):
                sale_order.team_id = int(self.env['ir.config_parameter'].sudo().get_param('ebay_sales_team'))
            currency = self.env['res.currency'].search([
                ('name', '=', transaction['TransactionPrice']['_currencyID'])])
            company_id = self.env.user.company_id
            IrDefault = self.env['ir.default']
            if variant.taxes_id:
                taxes_id = variant.taxes_id.ids
            else:
                taxes_id = IrDefault.get('product.template', 'taxes_id', company_id=company_id.id)
            sol = self.env['sale.order.line'].create({
                'product_id': variant.id,
                'order_id': sale_order.id,
                'name': self.name,
                'product_uom_qty': float(transaction['QuantityPurchased']),
                'product_uom': variant.uom_id.id,
                'price_unit': currency.compute(
                    float(transaction['TransactionPrice']['value']),
                    self.env.user.company_id.currency_id),
                'tax_id': [(6, 0, taxes_id)] if taxes_id else False,
            })
            sol._compute_tax_id()

            # create a sales order line if a shipping service is selected
            if 'ShippingServiceSelected' in transaction:
                taxes_id = IrDefault.get('product.template', 'taxes_id', company_id=company_id.id)
                shipping_name = transaction['ShippingServiceSelected']['ShippingService']
                shipping_product = self.env['product.template'].search([('name', '=', shipping_name)])
                if not shipping_product:
                    shipping_product = self.env['product.template'].create({
                        'name': shipping_name,
                        'uom_id': self.env.ref('product.product_uom_unit').id,
                        'type': 'service',
                        'categ_id': self.env.ref('sale_ebay.product_category_ebay').id,
                    })
                so_line = self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'name': shipping_name,
                    'product_id': shipping_product.product_variant_ids[0].id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('product.product_uom_unit').id,
                    'price_unit': currency.compute(
                        float(transaction['ShippingServiceSelected']['ShippingServiceCost']['value']),
                        company_id.currency_id),
                    'tax_id': [(6, 0, taxes_id)] if taxes_id else False,
                    'is_delivery': True,
                })
                so_line._compute_tax_id()
            sale_order.action_confirm()
            if 'BuyerCheckoutMessage' in transaction:
                sale_order.message_post(_('The Buyer Posted :\n') + transaction['BuyerCheckoutMessage'])
                sale_order.picking_ids.message_post(_('The Buyer Posted :\n') + transaction['BuyerCheckoutMessage'])
            if 'ShippingServiceSelected' in transaction:
                sale_order.picking_ids.message_post(
                    _('The Buyer Chose The Following Delivery Method :\n') + shipping_name)
            if 'order' in sale_order.order_line.filtered(
                    lambda line: not line._is_delivery()).mapped('product_id.invoice_policy'):
                sale_order.action_invoice_create(final=True)

    def _set_variant_url(self, item_id):
        variants = self.product_variant_ids.filtered('ebay_use')
        if len(variants) > 1 and self.ebay_listing_type == 'FixedPriceItem':
            for variant in variants:
                name_value_list = [{
                    'Name': self.ebay_product_template_id._ebay_encode(spec.attribute_id.name),
                    'Value': self._ebay_encode(spec.name)
                } for spec in variant.attribute_value_ids]
                call_data = {
                    'ItemID': item_id,
                    'VariationSpecifics': {
                        'NameValueList': name_value_list
                    }
                }
                item = self.ebay_execute('GetItem', call_data, backend_id=self.ebay_backend_id)
                variant.ebay_variant_url = item.dict()['Item']['ListingDetails']['ViewItemURL']

    def _compute_ebay_price(self):
        #ebay_api = self.env['ebay.backend'].search([('company_id', '=', self.env.user.company_id.id)])
        for record in self:
            ebay_api = record.ebay_backend_id
            pricelist_id = ebay_api.sudo().pricelist_id if ebay_api else self.env.user.company_id.pricelist_id
            currency_id = ebay_api.ebay_currency if ebay_api else self.env.user.company_id.currency_id
            if pricelist_id:
                product = record.sudo().ebay_product_template_id.product_variant_id.with_context(
                    quantity=1,
                    pricelist=pricelist_id.id,
                    currency_id=currency_id,
                )
                try:
                    record.calculated_ebay_price = product.price
                except:
                    record.calculated_ebay_price = product.price
            else:
                record.calculated_ebay_price = record.ebay_product_template_id.product_variant_id.list_price

    def tracking_ebay_price(self):
        self.ensure_one()
        tracking_id = self.env["shop.price.tracking"].create(
            {"price_track": "<h3 style='color:red;'>Price Tracking</h3>"})
        ebay_api = self.ebay_backend_id#self.env['ebay.backend'].search([('company_id', '=', self.env.user.company_id.id)])
        pricelist_id = ebay_api.sudo().pricelist_id if ebay_api else self.env.user.company_id.pricelist_id
        trackings = []
        if pricelist_id:
            res = pricelist_id.sudo().with_context(track=True)._compute_price_rule(
                list(pycompat.izip(self.ebay_product_template_id.product_variant_id, [1] * len(self), [False] * len(self))), flush=True)
            trackings = res[self.ebay_product_template_id.product_variant_id.id][3]
            track_info = self.ebay_product_template_id.product_variant_id._get_tracking_message(trackings)
            tracking_id.price_track = track_info

        return {
            'name': _('Price Tracking Information'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shop.price.tracking',
            'res_id': tracking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class ProductTemplate(models.Model):
    _inherit = "product.template"

    ebay_product_ids = fields.One2many('ebay.product.template', 'ebay_product_template_id', string='Ebay Products')