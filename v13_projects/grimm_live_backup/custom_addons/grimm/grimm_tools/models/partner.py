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
from email.utils import formataddr

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)

class ImportLogHistory(models.Model):
    """ Res Partner default Image for contact """
    _name = "import.log.history"
    _order = "create_date desc"

    _rec_name = "file_name"

    res_model = fields.Char('Model')
    file = fields.Binary('File', help="File to check and/or import, raw binary (not base64)", attachment=True)
    file_name = fields.Char('File Name')
    file_type = fields.Char('File Type')

class Import(models.TransientModel):
    """ Res Partner default Image for contact """
    _inherit = "base_import.import"

    def do(self, fields, columns, options, dryrun=False):
        import_result = super(Import, self).do(fields, columns, options, dryrun=dryrun)
        try:
            if import_result.get("ids", False) and not dryrun:
                log_vals = {'res_model': self.res_model, 'file':base64.b64encode(self.file), 'file_name':self.file_name, 'file_type':self.file_type}
                log_id = self.env["import.log.history"].sudo().create(log_vals)
        except:
            pass
        return import_result

class ResPartner(models.Model):
    """ Res Partner default Image for contact """
    _inherit = "res.partner"
    fax = fields.Char('Fax')

    def write(self, vals):
        for partner in self:
            if vals.get('credit_limit', partner.credit_limit) > partner.credit:
                vals.update({'sale_warn': 'warning',
                             'sale_warn_msg': 'Credit limit exceeded. Please talk to finance department for order approval'})
            else:
                vals.update({'sale_warn': 'no-message', 'sale_warn_msg': False})
        return super(ResPartner, self).write(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_special_price = fields.Html('AP', compute="_get_img_special_price",help="Special price is available for this Product.")
    avail_qty = fields.Html('Stock', compute="_get_avail_qty",help="frei")
    forecast_triplet = fields.Html('Avail.Qty', compute='_substring_forecast', help="<b><span style='color:#00b8d9;'>Available quantity</span> (<span style='color:#36b37e;'>physical stock</span><span style='color:#ff5630'>-open customer deliveries</span><span style='color:#ff991f'> + planned order receipts</span>)</b>")

    def _get_lang_specific_format(self, value):
        lang_obj = self.env["res.lang"].search([('code', '=', self._context.get("lang", "en_US"))])
        if lang_obj:
            return lang_obj.format("%.2f", value, grouping=True, monetary=False)
        return str(value)

    @api.depends('product_id')
    def _substring_forecast(self):
        self.forecast_triplet = ""
        for rec in self:
            if rec.product_id:
                rec.forecast_triplet = rec.product_id.forecast_triplet

    @api.depends('product_id')
    def _get_avail_qty(self):
        self.avail_qty = ""
        for line in self:
            if line.product_id.virtual_available > 0:
                line.avail_qty = _("<center style='background-color: forestgreen;border-radius: 10px;color: white;'><span style='margin-left:3px;margin-right:3px;'>%s</span></center>" % (line.product_id.virtual_available))


    def _get_special_info(self):
        res_value = 0
        if self.product_id.special_price_to:
            if (datetime.strptime(str(self.product_id.special_price_to), '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).date() < datetime.strptime(str(self.order_id.validity_date), '%Y-%m-%d').date() and (datetime.strptime(str(fields.Datetime.now()), '%Y-%m-%d %H:%M:%S')+ timedelta(hours=2)).date() <= (datetime.strptime(str(self.product_id.special_price_to), '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).date():
                res_value = 1
        else:
            res_value = 0
        return res_value

    @api.depends('product_id')
    def _get_img_special_price(self):
        for elem in self:
            if elem.product_id.special_price_from and elem.product_id.special_price_to:
                check_date = (datetime.strptime(str(fields.Datetime.now()), '%Y-%m-%d %H:%M:%S')+ timedelta(hours=2)).date()
                date_from = (datetime.strptime(str(elem.product_id.special_price_from), '%Y-%m-%d %H:%M:%S')+ timedelta(hours=2)).date()
                date_to = (datetime.strptime(str(elem.product_id.special_price_to), '%Y-%m-%d %H:%M:%S')+ timedelta(hours=2)).date()
                date_to_split = str(date_to).split("-")
                date_to_new = date_to_split[2]+"."+date_to_split[1]+"."+date_to_split[0]
                if date_from <= check_date <= date_to:
                    elem.is_special_price = "<center style='background-color: darkorange;border-radius: 10px;color: white;'><span style='white-space: nowrap;font-size: 10px;'><b> %.2f <br/><span style='margin-left:3px;margin-right:3px;'>%s</span> </b></span></center>" % (
                    elem.product_id.special_price,
                    str(date_to_new))
                else:
                    elem.is_special_price = ""
            else:
                elem.is_special_price = ""

    @api.onchange('product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        self.check_package_quantity()
        return res

    def check_package_quantity(self):
        if self.product_id.is_package:
            pack_qty = self.product_id.package_id.qty_no
            sale_qty = self.product_uom_qty
            left = self.product_uom_qty % pack_qty
            if left != 0:
                self.product_uom_qty = 0
                raise UserError(_("%s \n Produktverkauf nur in ganzen Verpackungseinheiten möglich. Menge %s nicht möglich. \nVerkaufsmenge muss %s oder ein vielfaches von %s sein." % (self.product_id.name,sale_qty,pack_qty,pack_qty)))

class IrMailServer(models.Model):
    """Represents an SMTP server, able to send outgoing emails, with SSL and TLS capabilities."""
    _inherit = "ir.mail_server"

    default_email = fields.Char(string='Default Target Email')
    is_default_email = fields.Boolean(string='Set Default Target Email',help="After activating this feature all email will be target to specified email address instead actual email. This feaure will e helpfull for test email related functionality.")

class MailMessage(models.Model):
    _inherit = 'mail.message'

    '''
    # Commented code related to issue for blank author id OD-725 #Odoo13Change
    @api.model
    def create(self, values):
        message = super(MailMessage, self).create(values)
        if not message.author_id and message.parent_id:
            if message.parent_id.partner_ids:
                partner_vals = {
                    'parent_id': message.parent_id.partner_ids[0].id,
                    'name': message.email_from,
                    'email': message.email_from[message.email_from.find('<') + 1:message.email_from.rfind('>')]
                }
                new_partner_id = self.env["res.partner"].sudo().create(partner_vals)
                message.author_id = new_partner_id.id
        return message
    '''

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send_prepare_values(self, partner=None):
        """Return a dictionary for specific email values, depending on a
        partner, or generic to the whole recipients given by mail.email_to.

            :param Model partner: specific recipient partner
        """
        self.ensure_one()
        body = self._send_prepare_body()
        body_alternative = tools.html2plaintext(body)
        if partner:
            if self._context.get("active_model","") == "account.move" or self.model == "account.move":
                email_to = [tools.formataddr((partner.name or 'False', partner.invoice_email if partner.invoice_email else partner.email or 'False'))]
            else:
                email_to = [tools.formataddr((partner.name or 'False', partner.email or 'False'))]
        else:
            email_to = tools.email_split_and_format(self.email_to)
        res = {
            'body': body,
            'body_alternative': body_alternative,
            'email_to': email_to,
        }
        return res

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
        IrMailServer = self.env['ir.mail_server']
        IrAttachment = self.env['ir.attachment']
        for mail_id in self.ids:
            success_pids = []
            failure_type = None
            processing_pid = None
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state != 'outgoing':
                    if mail.state != 'exception' and mail.auto_delete:
                        mail.sudo().unlink()
                    continue

                # remove attachments if user send the link with the access_token
                body = mail.body_html or ''
                attachments = mail.attachment_ids
                for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
                    attachments = attachments - IrAttachment.browse(int(link))

                # load attachment binary data with a separate read(), as prefetching all
                # `datas` (binary field) could bloat the browse cache, triggerring
                # soft/hard mem limits with temporary data.
                attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
                               for a in attachments.sudo().read(['name', 'datas', 'mimetype']) if
                               a['datas'] is not False]

                # specific behavior to customize the send email for notified partners
                email_list = []
                if mail.email_to:
                    email_list.append(mail._send_prepare_values())
                for partner in mail.recipient_ids:
                    values = mail._send_prepare_values(partner=partner)
                    values['partner_id'] = partner
                    email_list.append(values)

                # headers
                headers = {}
                ICP = self.env['ir.config_parameter'].sudo()
                bounce_alias = ICP.get_param("mail.bounce.alias")
                catchall_domain = ICP.get_param("mail.catchall.domain")
                if bounce_alias and catchall_domain:
                    if mail.mail_message_id.is_thread_message():
                        headers['Return-Path'] = '%s+%d-%s-%d@%s' % (
                        bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
                    else:
                        headers['Return-Path'] = '%s+%d@%s' % (bounce_alias, mail.id, catchall_domain)
                if mail.headers:
                    try:
                        headers.update(safe_eval(mail.headers))
                    except Exception:
                        pass

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback *after* actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                mail.write({
                    'state': 'exception',
                    'failure_reason': _(
                        'Error without exception. Probably due do sending an email without computed recipients.'),
                })
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to current
                # mail record.
                notifs = self.env['mail.notification'].search([
                    ('notification_type', '=', 'email'),
                    ('mail_id', 'in', mail.ids),
                    ('notification_status', 'not in', ('sent', 'canceled'))
                ])
                if notifs:
                    notif_msg = _(
                        'Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
                    notifs.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': 'UNKNOWN',
                        'failure_reason': notif_msg,
                    })
                    # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
                    # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    notifs.flush(fnames=['notification_status', 'failure_type', 'failure_reason'], records=notifs)

                # build an RFC2822 email.message.Message object and send it without queuing
                res = None
                for email in email_list:
                    email_to = email.get('email_to')
                    if mail.mail_server_id and mail.mail_server_id.is_default_email:
                        email_to = [mail.mail_server_id.default_email]
                    if not mail.mail_server_id:
                        search_server = IrMailServer.sudo().search([])
                        search_server = search_server.sorted(key=lambda r: r.sequence, reverse=True)
                        temp_list = []
                        for m_server in search_server:
                            if m_server.is_default_email:
                                temp_list.append(m_server.default_email)
                        if temp_list:
                            email_to = temp_list
                    params = self.env['ir.config_parameter'].sudo()
                    use_fixed_from_email = params.get_param("mail.use.fixed.sender")
                    if use_fixed_from_email: #GRIMM Changes to set default sender.
                        mail.email_from = params.get_param("mail.fixed.sender")
                    # Added this part to change mail server based on company id
                    company_mail_server = IrMailServer.sudo().search([('company_id', '=', mail.company_id.id)],limit=1)
                    if mail.mail_server_id:
                        mail.email_from = mail.mail_server_id.smtp_user
                        mail.reply_to = mail.mail_server_id.smtp_user
                    elif company_mail_server:
                        mail.mail_server_id = company_mail_server.id
                        mail.email_from = company_mail_server.smtp_user
                        mail.reply_to = company_mail_server.smtp_user

                    msg = IrMailServer.build_email(
                        email_from=mail.email_from,
                        email_to=email_to,
                        subject=mail.subject,
                        body=email.get('body'),
                        body_alternative=email.get('body_alternative'),
                        email_cc=tools.email_split(mail.email_cc),
                        reply_to=mail.reply_to,
                        attachments=attachments,
                        message_id=mail.message_id,
                        references=mail.references,
                        object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
                        subtype='html',
                        subtype_alternative='plain',
                        headers=headers)
                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = IrMailServer.send_email(
                            msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
                        if processing_pid:
                            success_pids.append(processing_pid)
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            failure_type = "RECIPIENT"
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                                         mail.message_id, email.get('email_to'))
                        else:
                            raise
                if res:  # mail has been sent at least once, no major exception occured
                    mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
                    _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
                    # /!\ can't use mail.state here, as mail.refresh() will cause an error
                    # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
                # instead of marking the mail as failed
                _logger.exception(
                    'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
                    mail.id, mail.message_id)
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs, chances are that the cursor
                # or SMTP session are unusable, causing further errors when trying to save the state.
                _logger.exception(
                    'Exception while processing mail with ID %r and Msg-Id %r.',
                    mail.id, mail.message_id)
                raise
            except Exception as e:
                failure_reason = tools.ustr(e)
                _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
                mail.write({'state': 'exception', 'failure_reason': failure_reason})
                mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason,
                                               failure_type='UNKNOWN')
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            # get the args of the original error, wrap into a value and throw a MailDeliveryException
                            # that is an except_orm, with name and value as arguments
                            value = '. '.join(e.args)
                        raise MailDeliveryException(_("Mail Delivery Failed"), value)
                    raise

            if auto_commit is True:
                self._cr.commit()
        return True


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_id=False, subtype=None, partner_ids=None, channel_ids=None,
                     attachments=None, attachment_ids=None,
                     add_sign=True, record_name=False,
                     **kwargs):
        if self._context.get('mail_post_autofollow') and partner_ids:
            partner_record_ids = self.env['res.partner'].sudo().search([('id', 'in', partner_ids), ('email', 'like', 'grimm-gastrobedarf.de')]).ids
            if partner_record_ids:
                self.message_subscribe(list(partner_record_ids))
        self = self.with_context(mail_post_autofollow=False)
        return super().message_post(
            body=body,
            subject=subject,
            message_type=message_type,
            email_from=email_from,
            author_id=author_id,
            parent_id=parent_id,
            subtype_id=subtype_id,
            subtype=subtype,
            partner_ids=partner_ids,
            channel_ids=channel_ids,
            attachments=attachments,
            attachment_ids=attachment_ids,
            add_sign=add_sign,
            record_name=record_name,
            **kwargs
        )

class FetchmailServer(models.Model):
    """Incoming POP/IMAP mail server account"""

    _inherit = 'fetchmail.server'
    fetch_fail_message = fields.Char("Fetch Failed reason")
    ignore_mail_domain = fields.Char("Ignore mail or domain (Comma seperated)")
    ignore_auto_reply = fields.Boolean("Ignore Auto-Reply", default=False)
    default_company_id = fields.Many2one("res.company", string="Default Company", help="This field will be set as company_id field after creation.")

    def fetch_mail(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.server_type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            import email
            if server.server_type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')

                        # GRIMM START
                        msg = email.message_from_bytes(data[0][1])

                        is_auto_reply = False
                        if server.ignore_auto_reply and (msg.get("X-Autoreply","").upper() in ["YES"] or msg.get("Auto-Submitted","").upper() in ["AUTO-REPLIED","AUTO-GENERATED"]):
                            is_auto_reply = True
                            self.env['auto.replied.email'].create_auto_replied_record(msg)

                        if server.ignore_mail_domain and not is_auto_reply:
                            ignore_mail_list = server.ignore_mail_domain.split(",")
                            received_from = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", msg.get("From", "")) # Getting email address from string like Dipak Suthar <d.suthar@grimm-gastrobedarf.de> will return only email
                            if received_from:
                                for ig_list in ignore_mail_list:
                                    if ig_list in received_from[0]:
                                        is_auto_reply = True
                        # GRIMM END

                        try:
                            if not is_auto_reply:
                                res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.server_type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                            self.env.cr.commit()
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages, server.server_type, server.name, (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True

#
#
#     def send_fetch_failure_email(self,message=False):
#         for this in self:
#             if message:
#                 this.fetch_fail_message = message
#             template = self.env.ref('grimm_tools.fetch_failed_email_template', raise_if_not_found=False)
#             email_list = self.env["ir.config_parameter"].get_param("blocked.job.emails", default=False)
#             if not email_list:
#                 email_list = "d.suthar@grimm-gastrobedarf.de"
#             template.email_to = email_list
#             if template:
#                 template.sudo().send_mail(this.id, force_send=True)
#
#     def fetch_mail(self):
#         """ WARNING: meant for cron usage only - will commit() after each email! """
#         additionnal_context = {
#             'fetchmail_cron_running': True
#         }
#         MailThread = self.env['mail.thread']
#         for server in self:
#             _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
#             additionnal_context['default_fetchmail_server_id'] = server.id
#             additionnal_context['server_type'] = server.server_type
#             count, failed = 0, 0
#             imap_server = None
#             pop_server = None
#             if server.server_type == 'imap':
#                 try:
#                     imap_server = server.connect()
#                     imap_server.select()
#                     result, data = imap_server.search(None, '(UNSEEN)')
#                     for num in data[0].split():
#                         res_id = None
#                         result, data = imap_server.fetch(num, '(RFC822)')
#                         imap_server.store(num, '-FLAGS', '\\Seen')
#                         try:
#                             res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
#                             if res_id and server.default_company_id:
#                                 try:
#                                     self.env[server.object_id.model].browse(res_id).company_id= server.default_company_id
#                                 except:
#                                     _logger.info('Failed to set company id for record %s server %s and record id is %s.', server.object_id.model, server.name,res_id, exc_info=True)
#                         except Exception:
#                             _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
#                             failed += 1
#                         imap_server.store(num, '+FLAGS', '\\Seen')
#                         self._cr.commit()
#                         count += 1
#                     _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
#                 except Exception as e:
#                     temp_msg = "General failure when trying to fetch mail from %s server %s.\n\n%s" % (server.server_type, server.name, str(e))
#                     self.send_fetch_failure_email(temp_msg)
#                     _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
#                 finally:
#                     if imap_server:
#                         imap_server.close()
#                         imap_server.logout()
#             elif server.server_type == 'pop':
#                 try:
#                     while True:
#                         pop_server = server.connect()
#                         (num_messages, total_size) = pop_server.stat()
#                         pop_server.list()
#                         for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
#                             (header, messages, octets) = pop_server.retr(num)
#                             message = (b'\n').join(messages)
#                             res_id = None
#                             try:
#                                 res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
#                                 if res_id and server.default_company_id:
#                                     try:
#                                         self.env[server.object_id.model].browse(res_id).company_id = server.default_company_id
#                                     except:
#                                         _logger.info('Failed to set company id for record %s server %s and record id is %s.',
#                                             server.object_id.model, server.name, res_id, exc_info=True)
#                                 pop_server.dele(num)
#                             except Exception:
#                                 _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
#                                 failed += 1
#                             self.env.cr.commit()
#                         if num_messages < MAX_POP_MESSAGES:
#                             break
#                         pop_server.quit()
#                         _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages, server.server_type, server.name, (num_messages - failed), failed)
#                 except Exception as e:
#                     temp_msg = "General failure when trying to fetch mail from %s server %s.\n\n%s" % (
#                         server.server_type, server.name, str(e))
#                     self.send_fetch_failure_email(temp_msg)
#                     _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
#                 finally:
#                     if pop_server:
#                         pop_server.quit()
#             server.write({'date': fields.Datetime.now()})
#         return True



class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def get_file_size(self, attachments,remove_id):
        if remove_id in attachments:
            attachments.remove(remove_id)
        attachment_ids = self.sudo().browse(attachments)
        filesize = 0
        for attach in attachment_ids:
            filesize = filesize + attach.file_size
        if filesize == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(filesize, 1000)))
        p = math.pow(1000, i)
        s = round(filesize / p, 2)
        return "%s  %s" % (s, size_name[i])

class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    payment_journal_id = fields.Many2one('account.journal', string='Default Payment Journal',help="This journal value will be selected when user do register payment on Invoices.",domain=[('type', 'in', ('bank', 'cash'))])

class AccountMove(models.Model):
    _inherit = 'account.move'

    # related_journal_id = fields.Integer(related='payment_mode_id.payment_journal_id.id')
    related_journal_id = fields.Integer(compute='_compute_related_journal_id')
    ref = fields.Char(string='Reference', copy=False, size=12)
    #is_final_invoice = fields.Boolean(string='Schlussrechnung')
    #final_invoice = fields.Boolean(string='Schlussrechnung')
    #state = fields.Selection(selection_add=[('partial', 'Teilrechnung')])
    #is_display_final_invoice = fields.Boolean(compute='_get_is_final_invoice_display')

    def action_post(self):
        products = self.mapped('invoice_line_ids.product_id.name')
        inv_type = self.mapped('type')
        if 'error article' in products and 'in_invoice' in inv_type:
            raise UserError(_("You can not post Invoice with 'error article'"))

        for inv in self:
            double_ref = self.search([('ref', '=', inv.ref)])
            if inv.type == 'in_invoice' and (not inv.ref or len(double_ref) >= 2):
                raise UserError(_("STOP. Either you haven't defined Invoice reference or reference is duplicate."))

        res = super(AccountMove, self).action_post()
        return res


    # def _get_is_final_invoice_display(self):
    #     for this in self:
    #         this.is_display_final_invoice = False
    #         invoice_ids = self.search([('invoice_origin', '=', this.invoice_origin), ('type', 'in', ['out_invoice','out_refund'])])
    #         if len(invoice_ids) > 1:
    #             this.is_display_final_invoice = True
    #
    # @api.onchange('is_final_invoice')
    # def _onchange_final_invoice(self):
    #     if self.is_final_invoice:
    #         invoice_ids = self.search([('invoice_origin', '=', self.invoice_origin), ('id', '!=', self._origin.id), ('type', 'in', ['out_invoice','out_refund'])])
    #         for inv in invoice_ids:
    #             inv.button_draft()
    #             inv.button_cancel()
    #             inv.state='partial'

    def _check_delivery_date(self):
        if self.delivery_date and self.invoice_date and self.type in ('out_invoice','out_refund') and self.delivery_date < self.invoice_date:
            warning = {
                'title': _("Delivery Date"),
                'message': _("The delivery date is before the invoice date. Please check and confirm your entries.")
            }
            return {'warning': warning}
        return False

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        res = super(AccountMove, self)._onchange_invoice_date()
        delivery_date = self._check_delivery_date()
        return delivery_date if delivery_date else res

    @api.onchange('delivery_date')
    def _onchange_delivery_date(self):
        delivery_date = self._check_delivery_date()
        return delivery_date

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # OVERRIDE
        # Recompute 'partner_shipping_id' based on 'partner_id'.
        addr = self.partner_id.address_get(['delivery'])
        self.partner_shipping_id = addr and addr.get('delivery') if not self.partner_shipping_id else self.partner_shipping_id

        res = super(AccountMove, self)._onchange_partner_id()

        # Recompute 'narration' based on 'company.invoice_terms'.
        if self.type == 'out_invoice':
            self.narration = self.company_id.with_context(lang=self.partner_id.lang).invoice_terms

        return res

    def _compute_related_journal_id(self):
        for record in self:
            default_journal_id = False
            if record.payment_mode_id:
                if record.payment_mode_id.payment_journal_id:
                    default_journal_id = record.payment_mode_id.payment_journal_id.id
            record.related_journal_id = default_journal_id if default_journal_id else False

    def serch_record(self,rec_model,origin):
        if origin:
            datas = self.env[rec_model].search([('name', '=', (origin).strip())])
            rec_id = False
            for data in datas:
                rec_id = data.id
            return rec_id

    def get_source_document(self):
        rec_id = False
        rec_model = False
        if self.invoice_origin and self.type == "out_invoice":
            data = self.serch_record('sale.order',self.invoice_origin)
            if data:
                rec_model = 'sale.order'
                rec_id = data
            else:
                data = self.serch_record('purchase.order', self.invoice_origin)
                if data:
                    rec_model = 'purchase.order'
                    rec_id = data
        elif self.invoice_origin and self.type == "in_invoice":
            data = self.serch_record('purchase.order', self.invoice_origin)
            if data:
                rec_model = 'purchase.order'
                rec_id = data
            else:
                data = self.serch_record('sale.order', self.invoice_origin)
                if data:
                    rec_model = 'sale.order'
                    rec_id = data
        else:
            data = self.serch_record('account.move', self.invoice_origin)
            if data:
                rec_model = 'account.move'
                rec_id = data
            else:
                data = self.serch_record('purchase.order', self.invoice_origin)
                if data:
                    rec_model = 'purchase.order'
                    rec_id = data
                else:
                    data = self.serch_record('sale.order', self.invoice_origin)
                    if data:
                        rec_model = 'sale.order'
                        rec_id = data

        if rec_id:
            return {
                'name': _('Source Document Record'),
                'view_mode': 'form',
                'res_id': rec_id,
                'res_model': rec_model,
                'type': 'ir.actions.act_window',
            }
        else:
            raise ValidationError(_('No source document available in odoo.'))

    def action_invoice_cancel_proforma(self):
        for invoice in self:
            invoice.state = 'draft'

class bi_wizard_product_bundle(models.TransientModel):
    _name = 'wizard.windelta.import'
    _description = 'Wizard windelta import'

    csv_file = fields.Binary('Browse File')
    filename = fields.Char('File name')
    order_id = fields.Many2one("sale.order")
    upload_info = fields.Html("Upload Information")

    @api.onchange('csv_file')
    def filename_change(self):
        if self.filename:
            extension = os.path.splitext(self.filename)[1]
            if extension.lower() == ".csv":
                upload_info = _("<center><h2 style='color:green;'>File is successfully uploaded.</h2></center>")
                line_list = []
                temp = NamedTemporaryFile()
                temp.write(base64.b64decode(self.csv_file))
                temp.seek(0)
                index = 1
                upload_info += _("<table width='80%' align='center' class='table'><thead><tr><th scope='col' width='20%'>No. </th><th scope='col'>Article SKU</th><th scope='col'>Status</th></tr></thead><tbody>")
                try:
                    with open(temp.name, 'r', encoding="ISO-8859-1") as inp:
                        next(inp, None)
                        for row in csv.reader(inp, delimiter=';'):
                            product_data = self.env["product.product"].search([('default_code', '=', (row[2]).strip())])
                            if product_data:
                                upload_info +="<tr><td>"+str(index)+"</td><td>"+str((row[2]).strip())+_("</td><td style='color:green;'>Available</td></tr>")
                                quantity = row[4]
                                vals = {'product_id': product_data.id, 'order_id': self.order_id.id,
                                        'product_uom_qty': quantity}
                                line_list.append(vals)
                            else:
                                upload_info += "<tr><td>"+str(index)+"</td><td>" + str((row[2]).strip()) + _("</td><td style='color:red;'>Not Available</td></tr>")
                            index +=1
                    upload_info += _("</tbody></table>")
                    self.upload_info = upload_info
                except Exception as e:
                    self.upload_info = _("<center><h2 style='color:red;'>Please upload valid file.</h2></center>")
                    raise UserError(_('Something went wrong with file or file is not valid.\n\n' + str(e)))
            else:
                self.upload_info = _("<center><h2 style='color:red;'>Please upload valid .csv file.</h2></center>")
        else:
            self.upload_info = _("<center><h2 style='color:red;'>Please upload file.</h2></center>")

    def import_windelta(self):
        temp = NamedTemporaryFile()
        temp.write(base64.b64decode(self.csv_file))
        temp.seek(0)
        try:
            with open(temp.name, 'r', encoding="ISO-8859-1") as inp:
                next(inp, None)
                for row in csv.reader(inp, delimiter=';'):
                    product_data = self.env["product.product"].search([('default_code', '=', (row[2]).strip())])
                    quantity = row[4]
                    if row[4].strip() == "":
                        quantity = 0
                    if product_data:
                        vals = {'product_id':product_data.id,'order_id':self.order_id.id,'product_uom_qty':quantity}
                        if row[0].lower() == "ja":
                            vals["name"] = (row[6]).strip()
                        line_data = self.env["sale.order.line"].create(vals)
                    else:
                        product_check = self.env["product.product"].search([('name', '=', 'error article')])
                        if product_check:
                            vals = {'product_id': product_check.id, 'order_id': self.order_id.id,'product_uom_qty': quantity,'name':(row[6]).strip()}
                            line_data = self.env["sale.order.line"].create(vals)
                        else:
                            vals = {'name': 'error article', 'sale_ok': True, 'purchase_ok': True, 'magento_type': 'simple'}
                            product_check = self.env["product.product"].create(vals)
                            if product_check:
                                vals = {'product_id': product_check.id, 'order_id': self.order_id.id,'product_uom_qty': quantity, 'name':(row[6]).strip()}
                                line_data = self.env["sale.order.line"].create(vals)
        except Exception as e:
            raise UserError(_('Something went wrong with file or file is not proper.\n\n'+str(e)))

