# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from lxml import etree
from lxml import objectify
from lxml.objectify import fromstring
from odoo import fields, models, _
from odoo.exceptions import UserError

def get_attachment_content(attachment):
    cfdi = base64.b64decode(attachment).decode()
    cfdi = cfdi.replace('xmlns:schemaLocation', 'xsi:schemaLocation')
    indx = cfdi.find('</cfdi:Comprobante>')
    cfdi = cfdi[0:indx+19]
    xml_signed = base64.b64encode(cfdi.encode('utf-8'))
    return xml_signed

class XmlImportWizard(models.TransientModel):
    _name = 'xml.import.wizard'
    _description = 'For import wizard'

    xml_import_invoice_id = fields.Many2one(
        comodel_name="xml.import.invoice",
        string="Xml invoice",
        required=True,
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Files',
        required=True,
    )

    def import_xml(self):
        for data_file in self.attachment_ids:
            xmlname = data_file.name.lower()
            xml = get_attachment_content(data_file.datas)
            if xmlname[-4:] == '.xml':
                self.xml_import_invoice_id.write({
                    'xml_table_ids': [(0, None, {
                        'xml': xml,
                        'name': xmlname
                    })]
                })
            else:
                raise UserError(
                    _('File %s is not xml type, please remove from list')
                    % (data_file.display_name)
                )
        if self.attachment_ids:
            self.xml_import_invoice_id.validate_xml()
        return True
