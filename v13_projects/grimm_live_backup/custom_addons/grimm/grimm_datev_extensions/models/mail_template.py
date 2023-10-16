# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import odoo
import smtplib
import base64
import psycopg2

from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import math
from tempfile import TemporaryFile, NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv
from datetime import datetime
from datetime import timedelta
import re
import tempfile
from email.utils import formataddr
from xml.dom import minidom, Node

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    send_xrechnung = fields.Boolean("XRechnung versenden", default=False)
    send_po_edi = fields.Boolean("Send Purchase EDI", default=False)

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    attach_edi_report = fields.Boolean("Attach EDI report", default=False)
    model_name = fields.Char("Model Name", related="model_id.model")

    def create_xml_file(self, po_id=False):
        if po_id:
            root = minidom.Document()

            ebestellung_node = root.createElement('ebestellung')
            root.appendChild(ebestellung_node)

            kopfdaten_node = root.createElement('Kopfdaten')
            ebestellung_node.appendChild(kopfdaten_node)

            bestelldatum_node = root.createElement('Bestelldatum')
            bestelldatum_node.appendChild(root.createTextNode(po_id.po_date.strftime('%Y-%m-%d') or ''))
            kopfdaten_node.appendChild(bestelldatum_node)

            bestellnummer_node = root.createElement('Bestellnummer')
            bestellnummer_node.appendChild(root.createTextNode(po_id.name))
            kopfdaten_node.appendChild(bestellnummer_node)

            '''
            #Optional
            sonderbestellung_node = root.createElement('Sonderbestellung')
            sonderbestellung_node.appendChild(root.createTextNode('Sonderbestellung'))
            kopfdaten_node.appendChild(sonderbestellung_node)
            '''

            lieferant_node = root.createElement('Lieferant')
            kopfdaten_node.appendChild(lieferant_node)

            lieferant_name_node = root.createElement('Name')
            lieferant_name_node.appendChild(root.createTextNode(po_id.dest_address_id.name))
            lieferant_node.appendChild(lieferant_name_node)

            lieferant_nummer_node = root.createElement('Nummer')
            lieferant_nummer_node.appendChild(root.createTextNode(po_id.dest_address_id.name))
            lieferant_node.appendChild(lieferant_nummer_node)

            lieferant_street_node = root.createElement('Strasse')
            lieferant_street_node.appendChild(root.createTextNode(po_id.dest_address_id.street or ''))
            lieferant_node.appendChild(lieferant_street_node)

            lieferant_zip_node = root.createElement('Postfach')
            lieferant_zip_node.appendChild(root.createTextNode(po_id.dest_address_id.zip or ''))
            lieferant_node.appendChild(lieferant_zip_node)

            lieferant_plz_node = root.createElement('Plz')
            lieferant_plz_node.appendChild(root.createTextNode(po_id.dest_address_id.zip or ''))
            lieferant_node.appendChild(lieferant_plz_node)

            lieferant_city_node = root.createElement('Ort')
            lieferant_city_node.appendChild(root.createTextNode(po_id.dest_address_id.city or ''))
            lieferant_node.appendChild(lieferant_city_node)

            lieferant_country_node = root.createElement('Land')
            lieferant_country_node.appendChild(root.createTextNode(po_id.dest_address_id.country_id.code if po_id.dest_address_id.country_id else ''))
            lieferant_node.appendChild(lieferant_country_node)

            lieferant_zeichen_node = root.createElement('IhrZeichen')
            # lieferant_zeichen_node.appendChild(root.createTextNode(po_id.dest_address_id.country_id.name or ''))
            lieferant_node.appendChild(lieferant_zeichen_node)

            lieferant_contact_node = root.createElement('Kontakt')
            lieferant_contact_node.appendChild(root.createTextNode(po_id.dest_address_id.name or ''))
            lieferant_node.appendChild(lieferant_contact_node)

            lieferant_email_node = root.createElement('E-Mail')
            lieferant_email_node.appendChild(root.createTextNode(po_id.dest_address_id.email or ''))
            lieferant_node.appendChild(lieferant_email_node)

            lieferant_phone_node = root.createElement('Telefon')
            lieferant_phone_node.appendChild(root.createCDATASection(po_id.dest_address_id.phone or ''))
            lieferant_node.appendChild(lieferant_phone_node)

            lieferant_ustid_node = root.createElement('USTID')
            lieferant_ustid_node.appendChild(root.createTextNode(po_id.dest_address_id.vat or ''))
            lieferant_node.appendChild(lieferant_ustid_node)

            lieferant_gln_node = root.createElement('GLN')
            lieferant_gln_node.appendChild(root.createTextNode('GLN'))
            lieferant_node.appendChild(lieferant_gln_node)

            auftraggeber_node = root.createElement('Auftraggeber')
            kopfdaten_node.appendChild(auftraggeber_node)

            auftraggeber_name_node = root.createElement('Name')
            auftraggeber_name_node.appendChild(root.createTextNode(po_id.dest_address_id.name))
            auftraggeber_node.appendChild(auftraggeber_name_node)

            auftraggeber_name2_node = root.createElement('Name2')
            auftraggeber_name2_node.appendChild(root.createTextNode(po_id.dest_address_id.parent_id.name if po_id.dest_address_id.parent_id else ''))
            auftraggeber_node.appendChild(auftraggeber_name2_node)

            auftraggeber_ustid_node = root.createElement('USTID')
            auftraggeber_ustid_node.appendChild(root.createTextNode(po_id.dest_address_id.vat or ''))
            auftraggeber_node.appendChild(auftraggeber_ustid_node)

            # optional
            # auftraggeber_tax_node = root.createElement('Steuernummer')
            # auftraggeber_tax_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # auftraggeber_node.appendChild(auftraggeber_tax_node)

            # optional
            # auftraggeber_gln_node = root.createElement('GLN')
            # auftraggeber_gln_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # auftraggeber_node.appendChild(auftraggeber_gln_node)

            # optional
            # auftraggeber_commision_node = root.createElement('Kommission')
            # auftraggeber_commision_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # auftraggeber_node.appendChild(auftraggeber_commision_node)

            # optional
            # auftraggeber_project_node = root.createElement('Projekt')
            # auftraggeber_project_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # auftraggeber_node.appendChild(auftraggeber_project_node)

            # optional
            # auftraggeber_bearbeiter_node = root.createElement('Bearbeiter')
            # auftraggeber_bearbeiter_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # auftraggeber_node.appendChild(auftraggeber_bearbeiter_node)

            auftraggeber_telephone_node = root.createElement('Telefon')
            auftraggeber_telephone_node.appendChild(root.createCDATASection(po_id.dest_address_id.phone or ''))
            auftraggeber_node.appendChild(auftraggeber_telephone_node)

            auftraggeber_email_node = root.createElement('E-Mail')
            auftraggeber_email_node.appendChild(root.createTextNode(po_id.dest_address_id.email or ''))
            auftraggeber_node.appendChild(auftraggeber_email_node)

            lieferadresse_node = root.createElement('Lieferadresse')
            kopfdaten_node.appendChild(lieferadresse_node)

            lieferadresse_name_node = root.createElement('Name')
            lieferadresse_name_node.appendChild(root.createTextNode(po_id.dest_address_id.name))
            lieferadresse_node.appendChild(lieferadresse_name_node)

            lieferadresse_name2_node = root.createElement('Name2')
            lieferadresse_name2_node.appendChild(root.createTextNode(po_id.dest_address_id.parent_id.name if po_id.dest_address_id.parent_id else ''))
            lieferadresse_node.appendChild(lieferadresse_name2_node)

            lieferadresse_street_node = root.createElement('Strasse')
            lieferadresse_street_node.appendChild(root.createTextNode(po_id.dest_address_id.street))
            lieferadresse_node.appendChild(lieferadresse_street_node)

            lieferadresse_plz_node = root.createElement('Plz')
            lieferadresse_plz_node.appendChild(root.createTextNode(po_id.dest_address_id.zip))
            lieferadresse_node.appendChild(lieferadresse_plz_node)

            lieferadresse_ort_node = root.createElement('Ort')
            lieferadresse_ort_node.appendChild(root.createTextNode(po_id.dest_address_id.city))
            lieferadresse_node.appendChild(lieferadresse_ort_node)

            lieferadresse_country_node = root.createElement('Land')
            lieferadresse_country_node.appendChild(root.createTextNode(po_id.dest_address_id.country_id.code if po_id.dest_address_id.country_id else ''))
            lieferadresse_node.appendChild(lieferadresse_country_node)

            # optional
            # lieferadresse_contact_node = root.createElement('Kontakt')
            # lieferadresse_contact_node.appendChild(root.createTextNode(po_id.company_id.vat))
            # lieferadresse_node.appendChild(lieferadresse_contact_node)

            # optional
            # lieferadresse_contact2_node = root.createElement('Kontakt2')
            # lieferadresse_contact2_node.appendChild(root.createCDATASection(po_id.company_id.phone))
            # lieferadresse_node.appendChild(lieferadresse_contact2_node)

            # optional delivery condition
            # liefer_condition_node = root.createElement('Lieferkonditionen')
            # kopfdaten_node.appendChild(liefer_condition_node)
            #
            # liefer_condition_termin_node = root.createElement('Liefertermin')
            # liefer_condition_termin_node.appendChild(root.createTextNode(po_id.company_id.name))
            # liefer_condition_node.appendChild(liefer_condition_termin_node)
            #
            # liefer_condition_fix_termin_node = root.createElement('Fixtermin')
            # liefer_condition_fix_termin_node.appendChild(root.createTextNode("0"))
            # liefer_condition_node.appendChild(liefer_condition_fix_termin_node)
            #
            # liefer_condition_versandart_node = root.createElement('Versandart')
            # liefer_condition_versandart_node.appendChild(root.createTextNode("0"))
            # liefer_condition_node.appendChild(liefer_condition_versandart_node)
            #
            # liefer_condition_lieferbedingung_node = root.createElement('Lieferbedingung')
            # liefer_condition_lieferbedingung_node.appendChild(root.createTextNode("0"))
            # liefer_condition_node.appendChild(liefer_condition_lieferbedingung_node)
            #
            # liefer_condition_lieferhinweis_node = root.createElement('Lieferhinweis')
            # liefer_condition_lieferhinweis_node.appendChild(root.createCDATASection("Fixtermin! Anlieferung bis 12 Uhr. Hebebühne ist vorhanden."))
            # liefer_condition_node.appendChild(liefer_condition_lieferhinweis_node)
            #
            # liefer_condition_lieferhinweis2_node = root.createElement('Lieferhinweis2')
            # liefer_condition_lieferhinweis2_node.appendChild(
            #     root.createCDATASection("Belegnummer und Kommission bitte unbedingt auf Auftragsbestätigung, Lieferschein und Rechnung vermerken! Lieferung bitte sofort. Vielen Dank."))
            # liefer_condition_node.appendChild(liefer_condition_lieferhinweis2_node)

            positionsdaten_node = root.createElement('Positionsdaten')
            ebestellung_node.appendChild(positionsdaten_node)

            for line in po_id.order_line:
                position_node = root.createElement('Position')
                positionsdaten_node.appendChild(position_node)

                positionsdaten_positionsnr_node = root.createElement('Positionsnr')
                positionsdaten_positionsnr_node.appendChild(root.createTextNode(str(line.line_no)))
                position_node.appendChild(positionsdaten_positionsnr_node)

                positionsdaten_artikelnnr_node = root.createElement('Artikelnnr')
                positionsdaten_artikelnnr_node.appendChild(root.createTextNode(line.vendor_code or ''))
                position_node.appendChild(positionsdaten_artikelnnr_node)

                # optional
                # positionsdaten_grimm_artikelnnr_node = root.createElement('PENTAGAST-Artikelnr')
                # positionsdaten_grimm_artikelnnr_node.appendChild(root.createTextNode(line.product_id.default_code))
                # position_node.appendChild(positionsdaten_grimm_artikelnnr_node)
                #
                # positionsdaten_gtin_node = root.createElement('GTIN')
                # positionsdaten_gtin_node.appendChild(root.createTextNode('GTIN'))
                # position_node.appendChild(positionsdaten_gtin_node)
                #
                # positionsdaten_commision_node = root.createElement('Kommission')
                # positionsdaten_commision_node.appendChild(root.createTextNode('Kommission'))
                # position_node.appendChild(positionsdaten_commision_node)

                positionsdaten_bezeichnung_node = root.createElement('Bezeichnung')
                position_node.appendChild(positionsdaten_bezeichnung_node)

                positionsdaten_bezeichnung1_node = root.createElement('Bezeichnung1')
                positionsdaten_bezeichnung1_node.appendChild(root.createTextNode(line.name or ''))
                positionsdaten_bezeichnung_node.appendChild(positionsdaten_bezeichnung1_node)

                # optional
                # positionsdaten_liefertermin_node = root.createElement('Liefertermin')
                # positionsdaten_liefertermin_node.appendChild(root.createTextNode('Liefertermin'))
                # position_node.appendChild(positionsdaten_liefertermin_node)

                positionsdaten_qty_node = root.createElement('Menge')
                positionsdaten_qty_node.appendChild(root.createTextNode(str(line.product_qty)))
                position_node.appendChild(positionsdaten_qty_node)

                positionsdaten_uom_node = root.createElement('Einheit')
                positionsdaten_uom_node.appendChild(root.createTextNode("Einheit"))
                position_node.appendChild(positionsdaten_uom_node)

                positionsdaten_price_unit_node = root.createElement('Einzelpreis')
                positionsdaten_price_unit_node.appendChild(root.createTextNode(str(line.price_unit)))
                position_node.appendChild(positionsdaten_price_unit_node)

                positionsdaten_price_sub_total_node = root.createElement('Gesamtpreis')
                positionsdaten_price_sub_total_node.appendChild(root.createTextNode(str(line.price_subtotal)))
                position_node.appendChild(positionsdaten_price_sub_total_node)

                # optional
                # positionsdaten_artikelrabattproz_node = root.createElement('Artikelrabattproz')
                # positionsdaten_artikelrabattproz_node.appendChild(root.createTextNode("Artikelrabattproz"))
                # position_node.appendChild(positionsdaten_artikelrabattproz_node)
                #
                # positionsdaten_artikelrabatt_node = root.createElement('Artikelrabatt')
                # positionsdaten_artikelrabatt_node.appendChild(root.createTextNode("Artikelrabatt"))
                # position_node.appendChild(positionsdaten_artikelrabatt_node)

                positionsdaten_bemerkung_node = root.createElement('Bemerkung')
                position_node.appendChild(positionsdaten_bemerkung_node)

            netto_node = root.createElement('Netto')
            netto_node.appendChild(root.createTextNode(str(po_id.amount_untaxed)))
            ebestellung_node.appendChild(netto_node)

            steuersatz_node = root.createElement('Steuersatz')
            steuersatz_node.appendChild(root.createTextNode("19"))
            ebestellung_node.appendChild(steuersatz_node)

            steuer_node = root.createElement('Steuer')
            steuer_node.appendChild(root.createTextNode(str(po_id.amount_tax)))
            ebestellung_node.appendChild(steuer_node)

            brutto_node = root.createElement('Brutto')
            brutto_node.appendChild(root.createTextNode(str(po_id.amount_total)))
            ebestellung_node.appendChild(brutto_node)

            gesamtrabattproz_node = root.createElement('Gesamtrabattproz')
            ebestellung_node.appendChild(gesamtrabattproz_node)

            gesamtrabatt_node = root.createElement('Gesamtrabatt')
            ebestellung_node.appendChild(gesamtrabatt_node)

            waehrung_node = root.createElement('Waehrung')
            waehrung_node.appendChild(root.createTextNode("EUR"))
            ebestellung_node.appendChild(waehrung_node)

            fussdaten_node = root.createElement('Fussdaten')
            ebestellung_node.appendChild(fussdaten_node)

            zahlungsbedingungen_node = root.createElement('Zahlungsbedingungen')
            zahlungsbedingungen_node.appendChild(root.createCDATASection("Zahlung XX Tage X% Skonto, XX Tage netto"))
            fussdaten_node.appendChild(zahlungsbedingungen_node)

            fusstext_node = root.createElement('Fusstext')
            fussdaten_node.appendChild(fusstext_node)

            fusstext2_node = root.createElement('Fusstext2')
            fusstext2_node.appendChild(root.createCDATASection("Es gelten ausschließlich unsere allgemeinen Geschäftsbedingungen. Preisänderungen bedürfen grundsätzlich unserer Zustimmung."))
            fussdaten_node.appendChild(fusstext2_node)

            fusstext3_node = root.createElement('Fusstext3')
            fusstext3_node.appendChild(root.createCDATASection(
                "Hauptsitz: Niederlassungen: E-Mail: Bankverbindungen:"))
            fussdaten_node.appendChild(fusstext3_node)

            xml_str = root.toprettyxml(indent="\t")
            print("XML string ====> ", xml_str)
            return xml_str

    def generate_email(self, res_ids, fields=None):
        result = super(MailTemplate, self).generate_email(res_ids=res_ids, fields=fields)
        if self.model_id.model == "account.move" and self.attach_edi_report:
            for k,v in result.items():
                if isinstance(v, dict) and v.get("res_id"):
                    invoice = self.env["account.move"].sudo().browse(v.get("res_id"))
                    if invoice.partner_id.send_xrechnung:
                        edi_xml_data = invoice._export_as_facturx_xml()
                        base64_data = base64.b64encode(edi_xml_data)
                        temp_list = [] #v.get("attachments",[])
                        temp_list.append(("%s_edi.xml"%invoice.name or "rechnung",base64_data))
                        v["attachments"] = temp_list
        if self.model_id.model == "purchase.order":
            for k,v in result.items():
                if isinstance(v, dict) and v.get("res_id"):
                    po_id = self.env["purchase.order"].sudo().browse(v.get("res_id"))
                    parent_partner = po_id.partner_id
                    while parent_partner.parent_id:
                        parent_partner = parent_partner.parent_id
                    if parent_partner.send_po_edi:
                        base64_data = base64.b64encode(self.create_xml_file(po_id=po_id).encode('utf-8'))
                        temp_list = v.get("attachments",[])
                        temp_list.append(("%s_edi.xml"%po_id.name,base64_data))
                        v["attachments"] = temp_list
        return result
