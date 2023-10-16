# -*- coding: utf-8 -*-

from odoo import models, api
import lxml.html as lxml_html
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def update_lead_from_e_mail(self):
        """ Update the new lead with data from the e-mail

        :return: True for updated, False for nothing updated
        """

        try:
            current_lead = self.browse(self._context.get('active_id', False))
            if current_lead and current_lead.message_ids:
                first_msg = current_lead.message_ids[0]
                body = lxml_html.fromstring(first_msg.body)
                texts = body.xpath('//div[@class="PlainText"]')

                if texts:
                    texts = body[0].text_content()
                    texts = texts.strip(' \r\n').split('\r\n', 3)
                    if len(texts) > 3:
                        name = texts[0].replace('Name: ', '')
                        mail = texts[1].replace('E-mail: ', '')
                        phone = texts[2].replace('Telephone: ', '')
                        comment = texts[3].replace('Comment: ', '').replace('\r\n', '', 1)
                        current_lead.update(
                            {'street': '', 'street2': '', 'zip': '', 'city': '', 'country_id': False,
                             'partner_name': ''})
                        partner = self.env['res.partner'].search([('email', '=', mail)], limit=1)
                        if partner:
                            current_lead.update({'partner_id': partner.id})
                            current_lead.onchange_partner_id(partner.id)
                        else:
                            current_lead.update({'partner_id': False})

                        current_lead.update(
                            {'contact_name': name, 'email_from': mail, 'phone': phone, 'description': comment})
                        return True
                    elif u'<h4>Kontaktdaten</h4>' in first_msg.body and u'<h4>Nachricht:</h4>' in first_msg.body:
                        texts = first_msg.body

                        vals = {}
                        start = texts.find(u'<h4>Kontaktdaten</h4>') + len(u'<h4>Kontaktdaten</h4>')
                        end = texts.find(
                            u'<h4>Nachricht:</h4>')
                        contact = texts[
                                  texts.find(u'<h4>Kontaktdaten</h4>') + len(u'<h4>Kontaktdaten</h4>'): texts.find(
                                      u'<h4>Nachricht:</h4>')]
                        contact.replace(u'<hr>', u'')
                        contact = lxml_html.fromstring(contact)
                        trs = contact.findall('.//tr')
                        for tr in trs:
                            td1 = tr[0]
                            td2 = tr[1]

                            if td1.text == u'Name':
                                vals['contact_name'] = td2.text
                            elif td1.text == u'Telefone':
                                vals['phone'] = td2.text
                            elif td1.text == u'Email':
                                vals['email_from'] = td2[0].text
                        message = texts[texts.find(u'<h4>Nachricht:</h4>') + len(u'<h4>Nachricht:</h4>'): texts.find(
                            u'Mit freundlichen Gr')]
                        message = lxml_html.fromstring(message)
                        vals['description'] = message.text
                        if vals:
                            current_lead.update(
                                {'street': '', 'street2': '', 'zip': '', 'city': '', 'country_id': False,
                                 'partner_name': ''})
                            if vals.get('email_from'):
                                partner = self.env['res.partner'].search([('email', '=', vals.get('email_from'))],
                                                                         limit=1)
                                if partner:
                                    current_lead.update({'partner_id': partner.id})
                                    current_lead.onchange_partner_id(partner.id)
                                else:
                                    current_lead.update({'partner_id': False})
                            current_lead.update(vals)
                    else:
                        pass
        except Exception as e:
            _logger.warning(str(e))
            return False
        return True
