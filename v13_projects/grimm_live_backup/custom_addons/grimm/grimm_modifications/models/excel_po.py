from odoo import api, fields, models, _
import csv
from io import StringIO
import re
import base64


class ExcelPO(models.Model):
    _inherit = 'purchase.order'

    def sorted_nicely_list(self, l):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    def get_sorted_line(self):
        """ Sort the given iterable in the way that humans expect."""
        line_seq_list = []
        final_list = []
        for line in self.order_line:
            if line.line_no:
                line_seq_list.append(str(line.line_no+str("***")+str(line.id))) #Added special char to split the id of order line.
            else:
                final_list.append(line)
        line_seq_list = self.sorted_nicely_list(line_seq_list)
        for l in line_seq_list:
            if "***" in l:
                line_id = l.split("***")[1]
                final_list.append(self.env["purchase.order.line"].browse(int(line_id)))
        return final_list


    # def write(self, vals):
    #     result = super(ExcelPO, self).write(vals)
    #     for res in self:
    #         line_seq_list = []
    #         line_seq_dict = {}
    #         for line in res.order_line:
    #             line_seq_list.append(str(line.line_no))
    #             line_seq_dict[line.id] =line.line_no
    #         print("Passing list =====> ", line_seq_list)
    #         line_seq_list = self.sorted_nicely_list(line_seq_list)
    #         print("Sorted list =====> ", line_seq_list)
    #         print("Dictionary ====> ", line_seq_dict)
    #         index = 1
    #         for l in line_seq_list:
    #             line_ids = [k for k,v in line_seq_dict.items() if v == l]
    #             for l_id in line_ids:
    #                 query = "update purchase_order_line set line_no_seq=%s where id=%s" % (index, l_id)
    #                 self._cr.execute(query)
    #                 index = index + 1
    #     return result

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        comp_id = self.env.user.company_id.id
        try:
            if self.env.context.get('send_rfq', False):
                if comp_id == 3:
                    template_id = ir_model_data.get_object_reference('grimm_modifications', 'email_template_edi_purchase_partenics')[1]
                else:
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            else:
                if comp_id == 3:
                    template_id = ir_model_data.get_object_reference('grimm_modifications', 'email_template_edi_purchase_done_partenics')[1]
                else:
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        # data = [['', '', self.company_id.name], ['', '', 'Bestellung: ' + self.name],
        #         ['', '', 'Datum: ' + self.po_date], ['Artikelnummer', 'Bestellmenge', 'Bezeichnung']]
        # select_seller = []
        # for field in self.order_line:
        #     selected = False
        #     for line_sel in field.product_id.seller_ids:
        #         if line_sel.product_name == field.product_id.name and selected is False and line_sel.name.name == self.partner_id.name:
        #             select_seller.append(line_sel)
        #             selected = True
        #
        #     if selected is False:
        #         select_seller.append(field.product_id.seller_ids[0])
        #
        # # print(select_seller)
        #
        # if select_seller:
        #     for line in [sel for sel in select_seller]:
        #         if line.product_code:
        #             if line.product_name:
        #                 data.append([line.product_code, field.product_qty, line.product_name])
        #             else:
        #                 data.append([line.product_code, field.product_qty, field.product_id.name])
        #         else:
        #             if line.product_name:
        #                 data.append([field.product_id.default_code, field.product_qty, line.product_name])
        #             else:
        #                 data.append([field.product_id.default_code, field.product_qty, field.product_id.name])
        #
        #
        # f = StringIO()
        # csv.writer(f, delimiter=';').writerows(data)
        # datas = base64.b64encode(f.getvalue().encode('utf-8'))
        # attachment = self.env['ir.attachment'].create(
        #     {'name': 'PO_' + self.name + '.csv', 'type': 'binary', 'datas': datas, 'extension': '.csv',
        #      'datas_fname': self.name + '.csv'})
        # # mail.attachment_ids = [(4, attachment.id)]grimm_reports
        # # print(attachment, attachment.name)
        # template = self.env['mail.template'].browse(template_id)
        # template.attachment_ids = [(6, 0, [attachment.id])]

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            #'custom_layout': "purchase.mail_template_data_notification_email_purchase_order",
            'purchase_mark_rfq_sent': True,
            'force_email': True,
            'company_id': comp_id
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
