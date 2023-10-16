from odoo import http, _, fields
from odoo.http import request

import logging
import base64
import json
from collections import OrderedDict
from datetime import datetime

_logger = logging.getLogger(__name__)


class MobileBarcodeController(http.Controller):

    @http.route('/mobile_barcode/mobile_main_menu', type='json', auth='user')
    def mobile_main_menu(self, data, **kw):
        """ Receive a barcode scanned from the main menu and return a dictionary upon which actions are taken"""

        barcode, model, serv_barcode = data.split('|')[0], data.split('|')[1], data.split('|')[2]
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', serv_barcode)], limit=1)

        if model == 'service':
            rec_service = task_id

            if len(rec_service) > 0:
                lst_var = []

                lst_rec = request.env['product.service.barcode'].sudo().search(
                    [('task', '=', serv_barcode), ('user_id', '=', request.env.context.get('uid'))])

                for rec in lst_rec:
                    lst_var.append({'barcode': rec.product_barcode, 'name': rec.product, 'qty': rec.qty})

                return {'service': {'service': self.format_parent_address(
                    self.empty_or_value(rec_service.claim_shipping_id.parent_id.name)) + self.empty_or_value(
                    rec_service.claim_shipping_id.name), 'product': lst_var}}
            else:
                return {'warning': _('It is not a service order')}
        else:
            rec_product = request.env['product.product'].sudo().search(
                ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)

            if rec_product:
                rec_exists = request.env['product.service.barcode'].sudo().search(
                    [('task', '=', serv_barcode), ('product', '=', rec_product.name),
                     ('user_id', '=', request.env.context.get('uid'))], limit=1)
                _logger.warning('CHECK IF EXISTS ' + str(len(rec_exists)))

                if not rec_exists:
                    vals = {
                        'product_barcode': barcode,
                        'prod_default_code': rec_product.default_code,
                        'task': serv_barcode,
                        'product': rec_product.name,
                        'qty': 1,
                        'task_id': task_id.id,
                        'user_id': request.env.context.get('uid'),
                    }
                    request.env['product.service.barcode'].sudo().create(vals)
                else:
                    rec_exists.write({'qty': rec_exists.qty + 1, 'transferred': False})

                lst_var = []
                lst_rec = request.env['product.service.barcode'].sudo().search(
                    [('task', '=', serv_barcode), ('user_id', '=', request.env.context.get('uid'))])

                for rec in lst_rec:
                    lst_var.append({'barcode': rec.product_barcode, 'name': rec.product, 'qty': rec.qty})
                return {'product': lst_var}
            else:
                return {'warning': _('Barcode ' + barcode + 'does not belong to any products!')}

    @http.route('/mobile_barcode/delete_product', type='json', auth='user')
    def delete_product(self, data, **kw):
        product, service = data.split('|')[0], data.split('|')[1]
        rec_exists = request.env['product.service.barcode'].sudo().search(
            [('task', '=', service), ('product_barcode', '=', product),
             ('user_id', '=', request.env.context.get('uid'))], limit=1)

        if rec_exists:
            rec_exists.sudo().unlink()

        lst_var = []
        lst_rec = request.env['product.service.barcode'].sudo().search(
            [('task', '=', service), ('user_id', '=', request.env.context.get('uid'))])

        for rec in lst_rec:
            lst_var.append({'barcode': rec.product_barcode, 'name': rec.product, 'qty': rec.qty})

        return {'product': lst_var}

    @http.route('/mobile_barcode/increase_prod_qty', type='json', auth='user')
    def increase_prod_qty(self, data, **kw):
        barcode, serv_barcode = data.split('|')[0], data.split('|')[1]
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', serv_barcode)], limit=1)
        rec_product = request.env['product.product'].sudo().search(
            ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)

        if rec_product:
            rec_exists = request.env['product.service.barcode'].sudo().search(
                [('task', '=', serv_barcode), ('product', '=', rec_product.name),
                 ('user_id', '=', request.env.context.get('uid'))], limit=1)

            if not rec_exists:
                vals = {
                    'product_barcode': barcode,
                    'prod_default_code': rec_product.default_code,
                    'task': serv_barcode,
                    'product': rec_product.name,
                    'qty': 1,
                    'task_id': task_id.id,
                    'user_id': request.env.context.get('uid'),
                }
                request.env['product.service.barcode'].sudo().create(vals)
            else:
                rec_exists.write({'qty': rec_exists.qty + 1, 'transferred': False})

            lst_var = []
            lst_rec = request.env['product.service.barcode'].sudo().search(
                [('task', '=', serv_barcode), ('user_id', '=', request.env.context.get('uid'))])

            for rec in lst_rec:
                lst_var.append({'barcode': rec.product_barcode, 'name': rec.product, 'qty': rec.qty})
            return {'product': lst_var}
        else:
            return {'warning': _('Barcode ' + barcode + 'does not belong to any products!')}

    @http.route('/mobile_barcode/decrease_prod_qty', type='json', auth='user')
    def decrease_prod_qty(self, data, **kw):
        product, service = data.split('|')[0], data.split('|')[1]
        rec_exists = request.env['product.service.barcode'].sudo().search(
            [('task', '=', service), ('product_barcode', '=', product),
             ('user_id', '=', request.env.context.get('uid'))], limit=1)

        if rec_exists:
            if rec_exists.qty == 1:
                rec_exists.sudo().unlink()
            else:
                rec_exists.write({'qty': rec_exists.qty - 1, 'transferred': False})

        lst_var = []
        lst_rec = request.env['product.service.barcode'].sudo().search(
            [('task', '=', service), ('user_id', '=', request.env.context.get('uid'))])

        for rec in lst_rec:
            lst_var.append({'barcode': rec.product_barcode, 'name': rec.product, 'qty': rec.qty})

        return {'product': lst_var}

    def format_parent_address(self, address):
        return address + ', ' if address else ''

    def empty_or_value(self, val):
        return val if val else ''

    @http.route('/mobile_barcode/get_customer_info', type='json', auth='user')
    def get_customer_info(self, service, **kw):
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
        if task_id.partner_id.street:
            address = task_id.partner_id.street
            address = '+'.join(address.split(' '))
            address += '+' + task_id.partner_id.zip
        else:
            address = ''
        info_dict = {}
        if task_id:
            info_dict.update({'name': self.format_parent_address(
                self.empty_or_value(task_id.claim_shipping_id.parent_id.name)) + self.empty_or_value(
                task_id.claim_shipping_id.name), 'street': task_id.partner_id.street,
                              'zip': task_id.partner_id.zip, 'phone': self.empty_or_value(task_id.partner_id.phone),
                              'mobile': self.empty_or_value(task_id.partner_id.mobile),
                              'contact': self.empty_or_value(task_id.claim_contact.name),
                              'cphone': self.empty_or_value(task_id.claim_contact.phone), 'address': address})
            _logger.info('CUSTOMER INFO: ' + str(len(info_dict)))
        return {'info': info_dict}

    @http.route('/mobile_barcode/upload_attachments', type='http', auth='user', csrf=False)
    def upload_attachments(self, **post):
        filename = post.get('beleg_info').filename

        if filename:
            service = post.get('serv_code_hidden')
            file = post.get('beleg_info')
            task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)

            attachment_vals = {
                'name': filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'project.task',
                'res_id': task_id.id,
            }

            attachment = request.env['ir.attachment'].create(attachment_vals)
            _logger.info('Attachment created ' + str(len(attachment)))

    @http.route('/mobile_barcode/upload_signature', type='json', auth='user')
    def upload_signature(self, data, **post):
        file, service = data.split('|')[0], data.split('|')[1]
        filename = service + '.png'
        file = file.split(',')[1]
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)

        attachment_vals = {
            'name': filename,
            'datas': bytes(file, 'utf-8'),
            'res_model': 'project.task',
            'res_id': task_id.id,
        }

        attachment = request.env['ir.attachment'].create(attachment_vals)

        if attachment:
            return {'info': _('Signature has been added as an attachment')}
        else:
            return {'warning': _('Oops! Something went wrong!')}

    @http.route('/mobile_barcode/st_checkboxes', type='json', auth='user')
    def st_checkboxes(self, data, **post):
        chkbx_id, chkbx_val, service = data.split('|')[0], data.split('|')[1], data.split('|')[2]
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
        serv_rec = request.env['service.travel'].sudo().search(
            [('task_id', '=', task_id.id), ('user_id', '=', request.env.context.get('uid'))], limit=1)
        chkbx_val = json.loads(chkbx_val.lower())

        res = False
        if serv_rec:
            serv_rec.write({chkbx_id: chkbx_val})
        else:
            res = request.env['service.travel'].sudo().create(
                {'task_id': task_id.id, 'user_id': request.env.context.get('uid'), chkbx_id: chkbx_val})

        if serv_rec or res:
            return {'info': _('Success!')}
        else:
            return {'warning': _('Oops! Something went wrong!')}

    @http.route('/mobile_barcode/create_timesheet', type='json', auth='user')
    def create_timesheet(self, data, **post):
        timesheet_data = data.split('|')
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', timesheet_data[0])], limit=1)
        serv_rec = request.env['service.travel.timesheet'].sudo().search(
            [('task_id', '=', task_id.id), ('user_id', '=', int(timesheet_data[5]))], limit=1)

        if not serv_rec:
            vals_create = {
                'other_material': timesheet_data[1],
                'date': datetime.strptime(timesheet_data[2], '%m/%d/%Y'),
                'duration': timesheet_data[3] if timesheet_data[3] != 'null' else 0.0,
                'travel_cost': timesheet_data[4],
                'task_id': task_id.id,
                'user_id': int(timesheet_data[5])
            }
            print(vals_create)
            timesheet_rec = request.env['service.travel.timesheet'].sudo().create(vals_create)
        else:
            vals_write = {
                'other_material': timesheet_data[1],
                'date': datetime.strptime(timesheet_data[2], '%m/%d/%Y'),
                'duration': timesheet_data[3] if timesheet_data[3] != 'null' else 0.0,
                'travel_cost': timesheet_data[4],
            }
            timesheet_rec = serv_rec.sudo().write(vals_write)

        self.add_timesheet_entries(timesheet_data[2], timesheet_data[1],
                                   timesheet_data[3] if timesheet_data[3] != 'null' else 0.0, task_id.id,
                                   timesheet_data[4], int(timesheet_data[5]))

        print(timesheet_rec)
        if timesheet_rec:
            return {'info': _('Success!')}
        else:
            return {'warning': _('Oops! Something went wrong!')}

    # @http.route('/mobile_barcode/other_material', type='json', auth='user')
    # def other_material(self, data, **post):
    #     other_material, service = data.split('|')[0], data.split('|')[1]
    #     task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
    #     serv_rec = request.env['service.travel'].sudo().search(
    #         [('task_id', '=', task_id.id), ('user_id', '=', request.env.context.get('uid'))], limit=1)
    #
    #     res = False
    #     if serv_rec:
    #         serv_rec.write({'other_material': other_material})
    #     else:
    #         res = request.env['service.travel'].sudo().create(
    #             {'task_id': task_id.id, 'user_id': request.env.context.get('uid'), 'other_material': other_material})
    #
    #     self.add_timesheet_entries(datepicker=False, description=other_material, duration=0.0, task_id=task_id.id)
    #
    #     if serv_rec or res:
    #         return {'info': _('Success!')}
    #     else:
    #         return {'warning': _('Oops! Something went wrong!')}

    # @http.route('/mobile_barcode/datepicker', type='json', auth='user')
    # def datepicker(self, data, **post):
    #     datepicker, service = data.split('|')[0], data.split('|')[1]
    #     task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
    #     serv_rec = request.env['service.travel'].sudo().search(
    #         [('task_id', '=', task_id.id), ('user_id', '=', request.env.context.get('uid'))], limit=1)
    #
    #     res = False
    #     if serv_rec:
    #         serv_rec.write({'date': datepicker})
    #     else:
    #         res = request.env['service.travel'].sudo().create(
    #             {'task_id': task_id.id, 'user_id': request.env.context.get('uid'), 'date': datepicker})
    #
    #     self.add_timesheet_entries(datepicker=datepicker, description='', duration=0.0, task_id=task_id.id)
    #
    #     if serv_rec or res:
    #         return {'info': _('Success!')}
    #     else:
    #         return {'warning': _('Oops! Something went wrong!')}
    #
    # @http.route('/mobile_barcode/duration', type='json', auth='user')
    # def duration(self, data, **post):
    #     duration, service = data.split('|')[0], data.split('|')[1]
    #     task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
    #     serv_rec = request.env['service.travel'].sudo().search(
    #         [('task_id', '=', task_id.id), ('user_id', '=', request.env.context.get('uid'))], limit=1)
    #
    #     if duration == 'null':
    #         duration = 0.0
    #
    #     res = False
    #     if serv_rec:
    #         serv_rec.write({'duration': duration})
    #     else:
    #         res = request.env['service.travel'].sudo().create(
    #             {'task_id': task_id.id, 'user_id': request.env.context.get('uid'), 'duration': duration})
    #
    #     self.add_timesheet_entries(datepicker=False, description='', duration=duration, task_id=task_id.id)
    #
    #     if serv_rec or res:
    #         return {'info': _('Success!')}
    #     else:
    #         return {'warning': _('Oops! Something went wrong!')}

    def add_timesheet_entries(self, datepicker, description, duration, task_id, travel_cost, user_id):
        loggedin_usr = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)

        # _logger.info('LoogedIn use-a' + str(loggedin_usr.name) + str(request.env.context.get('uid')))
        timesheet_ids_rec = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', loggedin_usr.id), ('task_id', '=', task_id)], limit=1)

        # print('TM', timesheet_ids_rec, datepicker, description, duration, task_id, travel_cost, user_id,
        #       loggedin_usr.id)
        if not timesheet_ids_rec:
            vals_timesheet = {
                'employee_id': loggedin_usr.id,
                'date': datetime.strptime(datepicker, '%m/%d/%Y'),
                'account_id': 5,
                'task_id': task_id,
                'unit_amount': duration if duration != 0.0 else 0.0,
                'name': description if description != '' else '',
                'travel_cost': travel_cost
            }
            # print('New Timesheet: ', vals_timesheet)
            request.env['account.analytic.line'].sudo().create(vals_timesheet)
        else:
            vals_timesheet = {
                'employee_id': loggedin_usr.id,
                'date': datetime.strptime(datepicker, '%m/%d/%Y'),
                'unit_amount': duration if duration != 0.0 else 0.0,
                'name': description if description != '' else '',
                'travel_cost': travel_cost
            }
            timesheet_ids_rec.write(vals_timesheet)

    @http.route('/mobile_barcode/get_service_info', type='json', auth='user')
    def get_service_info(self, service, **kw):
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
        serv_rec = request.env['service.travel'].sudo().search(
            [('task_id', '=', task_id.id), ('user_id', '=', request.env.context.get('uid'))], limit=1)

        # date_for_ui = ''
        # if serv_rec.date:
        #     date_for_ui = serv_rec.date.split(' ')[0]
        #     date_for_ui_arr = date_for_ui.split('-')
        #     date_for_ui = date_for_ui_arr[1] + '/' + date_for_ui_arr[2] + '/' + date_for_ui_arr[0]

        info_dict = {
            # 'st_ap_1': str(serv_rec.st_ap_1).lower(),
            # 'st_ap_2': str(serv_rec.st_ap_2).lower(),
            # 'st_anfahrt': str(serv_rec.st_anfahrt).lower(),
            'st_small_pieces': str(serv_rec.st_small_pieces).lower(),
            'st_meters_pack': str(serv_rec.st_meters_pack).lower(),
            'st_clean_and_care': str(serv_rec.st_clean_and_care).lower(),
            # 'duration': serv_rec.duration,
            # 'other_material': serv_rec.other_material if serv_rec.other_material else '',
            # 'date': date_for_ui,
        }

        # print('Returned Dict ', info_dict)
        return {'service': info_dict}

    @http.route('/mobile_barcode/get_service_ticket', type='json', auth='user')
    def get_service_ticket(self, state, **kw):
        # At the moment, the stages ids are hardcoded. If we need to add or remove states, changes has to be done on the JavaScript side as well.
        hardcoded_stage_dict = {
            'Neu': 5,
            'Ersatzteile Bestellt': 23,
            'Techniker': 22
        }
        service_recs = request.env['project.task'].sudo().search(
            [('stage_id.id', '=', hardcoded_stage_dict.get(state)), ('user_id', '=', request.env.context.get('uid'))])

        lst_service_recs = []
        if service_recs:
            for rec in service_recs:
                date_for_ui = ''
                if rec.create_date:
                    date_for_ui = '%s/%s/%s' % (rec.create_date.strftime('%m'), rec.create_date.strftime('%d'), rec.create_date.strftime('%Y'))

                info_dict = OrderedDict()
                info_dict['customer'] = rec.partner_id.name
                info_dict['date'] = date_for_ui
                info_dict['barcode'] = rec.name_seq

                lst_service_recs.append(info_dict)

            return {'ticket': lst_service_recs}
        else:
            return {'warning': 'No record found!'}

    @http.route('/mobile_barcode/change_ticket_state', type='json', auth='user')
    def change_ticket_state(self, data, **kw):
        service, state = data.split('|')[0], data.split('|')[1]
        print('Data', service, state)
        # state_lst = ['Neu', 'Ersatzteile Bestellt', 'Techniker']
        hardcoded_stage_dict = {
            '29': 'Neu',
            '23': 'Ersatzteile Bestellt',
            '22': 'Techniker',
            '19': 'Fertig'
        }
        service_recs = request.env['project.task'].sudo().search([('name_seq', '=', service)])

        if service_recs:
            for rec in service_recs:
                rec.sudo().write({'stage_id': int(state)})

            return {'notify': 'Changed status to ' + hardcoded_stage_dict.get(state)}
        else:
            return {'warning': 'Record does not exist or has been deleted!'}

    @http.route('/mobile_barcode/get_service_users', type='json', auth='user')
    def get_service_users(self, **kw):
        serv_group = request.env['res.groups'].sudo().search([('name', '=', 'Service App Group')])
        lst_serv_users = []
        for usr in serv_group.users:
            selected = 'selected="true"' if usr.id == request.env.uid else ''
            lst_serv_users.append('<option ' + selected + ' value="' + str(usr.id) + '">' + usr.name + '</option>')

        print('Service Users List ', lst_serv_users)
        return {'users': lst_serv_users}

    @http.route('/mobile_barcode/get_timesheets', type='json', auth='user')
    def get_timesheets(self, service, **kw):
        task_id = request.env['project.task'].sudo().search([('name_seq', '=', service)], limit=1)
        service_travel = request.env['service.travel.timesheet'].sudo().search([('task_id', '=', task_id.id)])

        print('SV', service_travel, service)
        lst_timesheets = []
        if service_travel:
            for rec in service_travel:
                date_for_ui = ''
                if rec.date:
                    # date_for_ui = rec.date.split(' ')[0]
                    # date_for_ui_arr = date_for_ui.split('-')
                    date_for_ui = '%s/%s/%s' % (rec.date.strftime('%m'), rec.date.strftime('%d'), rec.date.strftime('%Y'))
                    # date_for_ui = date_for_ui_arr[1] + '/' + date_for_ui_arr[2] + '/' + date_for_ui_arr[0]

                loggedin_usr = request.env['hr.employee'].sudo().search([('user_id', '=', rec.user_id.id)], limit=1)
                lst_timesheets.append('<tr><td>' + date_for_ui + '</td><td class="zero-padding">' + str(
                    rec.duration) + '</td><td class="zero-padding">' + str(
                    loggedin_usr.name) + '</td><td class="zero-padding desc-width">' + rec.travel_cost + '</td></tr>')

        print('Timesheets List ', lst_timesheets)
        return {'timesheets': lst_timesheets}
