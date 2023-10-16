# -*- coding: utf-8 -*-

import base64
import copy
import logging

import lxml.html as lxml_html
import requests
from openerp import models, api, _
from openerp.exceptions import MissingError

_logger = logging.getLogger(__name__)


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.model
    def update_claim_from_e_mail(self):
        """ Update the new claim with data from the e-mail

        :return: True for updated, False for nothing updated
        """
        claim = self.browse(self._context.get('active_id', False))
        if claim and claim.message_ids:
            first_msg = claim.message_ids[0]
            mapping_contact = {'Ansprechpartner': 'contact_name', 'Firma': 'company_name',
                               'Kundennummer (falls vorhanden)': 'ref', 'Telefon': 'phone',
                               'E-Mail-Adresse': 'email', u'Straße': 'street', u'Nummer': 'street_number', 'PLZ': 'zip',
                               'Ort': 'city'}
            contact_vals = {}
            vals = {}
            images = {}
            device_typ, manufacturer = '', ''

            def parse_empty():
                raise MissingError('Function not implemented.')

            def parse_customer_information(key, child):
                if key in mapping_contact and child.tail:
                    contact_vals[mapping_contact[key]] = child.tail

            def parse_description(key, child):
                if child.tail:
                    if key == u'Zusätzliche Hinweise':
                        vals['description'] = u'<p>{}</p>{}'.format(child.tail, vals['description'])
                    else:
                        vals['description'] = u'{}<p>{}: {}</p>'.format(vals.get('description', ''), key, child.tail)

            try:
                body = lxml_html.fromstring(first_msg.body)
                for node in body.findall(".//h1/..[@valign='top']"):
                    key, value = '', ''
                    func = parse_empty
                    for child in node:
                        if child.tag == 'h2':
                            if child.text == u'Ihre Angaben':
                                # part 1: customer information
                                func = parse_customer_information
                            elif child.text == u'Daten zum Gerät':
                                # part 2: device information
                                func = parse_description
                            elif child.text == u'Produktfoto oder Skizze':
                                # part 3: fotos
                                func = None
                            else:
                                _logger.warning("This part is not implemented")
                                continue
                        elif func is None:
                            if child.tag == 'a':
                                image_link = child.attrib.get('href', None)
                                images[image_link] = child.text

                        elif child.tag == 'b':
                            key = child.text
                        elif child.tag == 'br':
                            """
                            if key == u'Geräteart':
                                device_typ = child.tail
                            elif key == u'Hersteller':
                                manufacturer = child.tail
                            """
                            func(key, child)
                    street = contact_vals.pop('street') + ' ' + contact_vals.pop('street_number')
                    contact_vals['street'] = street

                    filter = [('email', '=', contact_vals['email'])]
                    if 'ref' in contact_vals:
                        filter.append(('ref', '=', contact_vals.pop('ref')))

                    contact = self.env['res.partner'].search(filter, limit=1)
                    if not contact:
                        company_vals = copy.deepcopy(contact_vals)
                        company_vals['name'] = company_vals.pop('company_name')
                        company_vals.pop('contact_name')
                        company_vals.update({'is_company': True, 'company_type': 'company', 'customer': True})
                        company = self.env['res.partner'].create(company_vals)
                        contact_vals.pop('company_name')
                        contact_vals['name'] = contact_vals.pop('contact_name')
                        contact_vals.update(
                            {'is_company': False, 'company_type': 'person', 'type': 'contact', 'customer': True,
                             'parent_id': company.id})
                        contact = self.env['res.partner'].create(contact_vals)

                    category = self.env['crm.claim.category'].search([('name', '=', 'Ersatzteilanfrage')], limit=1)
                    if not category:
                        category = self.env['crm.claim.category'].create({'name': 'Ersatzteilanfrage'})

                    vals.update({'partner_id': contact.id, 'partner_phone': contact_vals.get('phone', ''),
                                 'email_from': contact_vals['email'],
                                 'name': _('Part inquiry %s %s') % (device_typ, manufacturer),
                                 'categ_id': category.id})
                    claim.write(vals)

                    first_msg.attachment_ids = [(0, 0, {'name': name,
                                                        'datas_fname': name,
                                                        'datas': base64.b64encode(requests.get(image_link).content),
                                                        'typ': 'binary', }) for image_link, name in images.iteritems()]
                    return True
            except:
                raise

            return False
        return False
