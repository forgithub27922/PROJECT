# -*- coding: utf-8 -*-
##############################################################################
#
# Skyscend Business Soluitions
# Copyright (C) 2019  (http://www.skyscendbs.com)
#
# Skyscend Business Soluitions Pvt. Ltd.
# Copyright (C) 2020  (http://www.skyscendbs.com)
##############################################################################
from odoo import models, fields, api, exceptions, _
from . import base
import pytz
import logging

_logger = logging.getLogger(__name__)


@api.model
def _tz_get(self):
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


def bioetric_getattendance(ip, port, timezone=False):
    """
    To Get attendance from the Biometric Device.
    """
    zk = base.ZK(ip, port, timeout=60, password=0, force_udp=False, ommit_ping=False)
    conn = zk.connect()
    conn.enable_device()
    attendances = conn.get_attendance()
    return attendances if attendances else None


class bio_config(models.Model):
    """
    Biometric configuration
    """
    _name = "bio.config"
    _description = "Biometric Configuration"
    _rec_name = "bioip"

    bioip = fields.Char(string='Biometric IP address', translate=True)
    bioport = fields.Char(string='Biometric Port', default=4370, translate=True)
    bio_tz = fields.Selection(_tz_get, string='Biometric Timezone', default="Asia/Calcutta")  # For the biometric Device Timezone

    @api.constrains('bioport', 'bioip')
    def _check_biometric(self):
        """
         Constrains for the biometric PORT & IP
        """
        for ids in self:
            if ids.bioport:
                bio_port = ids.bioport
                if bio_port.isdigit():
                    if (len(bio_port) > 4) or (len(bio_port) < 2):
                        raise exceptions.ValidationError(_('Biometric port length is should not be less than 2 and not be greater then 4.'))
                else:
                    raise exceptions.ValidationError(_('Biometric port must be in digit.'))

            if ids.bioip:
                bio_ip = ids.bioip
                if (len(bio_ip.split(".")) != 4):
                    raise exceptions.ValidationError(_('Biometric ip length is should not be less than 4.'))
                else:
                    if len(bio_ip.split(".")) == 4:
                        for xips in bio_ip.split("."):
                            if xips.isdigit():
                                if (not len(xips)) or (len(xips) > 3):
                                    raise exceptions.ValidationError(_('Biometric ip digit length is should not be  zero or not be greater than 3.'))
                            else:
                                raise exceptions.ValidationError(_('Biometric ip must be in the digit.'))

    @api.multi
    def attendance_manager(self):
        """
        To manage and Sort according to datetime into UTC timezone
        """
        bio_config_obj = self.env["bio.config"].search([])
        attendance_list = []
        new_l = []
        last_attn = self.env["last.attn"].sudo().search([], order='last_dt DESC', limit=1)

        if bio_config_obj:
            try:
                for x in bio_config_obj:
                    attendance_rec = bioetric_getattendance(x.bioip, int(x.bioport))
                    for data in attendance_rec:
                        local_dt_utc = (pytz.timezone(x.bio_tz).localize(data.get('timestamp')).astimezone(pytz.utc).replace(tzinfo=None))
                        if last_attn:
                            if local_dt_utc > last_attn.last_dt:
                                attendance_list.append({'timestamp':local_dt_utc, 'userid':data.get('userid')})
                        else:
                            attendance_list.append({'timestamp':local_dt_utc, 'userid':data.get('userid')})
            except:
                pass
     
        if attendance_list:  # To remove duplicate Dictionary Attendance
            seen = set()
            for d in attendance_list:
                t = tuple(d.items())
                if t not in seen:
                    seen.add(t)
                    new_l.append(d)
                      
        final_att = []
        if new_l :
            for x in sorted(new_l, key=lambda elem: "%s" % (elem['timestamp'])):
                final_att.append({
                                 'attendances':x.get('timestamp'),
                                 'userid':x.get('userid'),
                                  })
        return final_att if final_att else None

    @api.multi
    def _cron_biometric(self):  
        """
        Update attendance.csv into the Odoo v12
        """
        attendances = self.attendance_manager()
        attendance_list = []
        empid = self.env['hr.employee'].search([])
        attendanceobj = self.env['hr.attendance'].search([])
        if attendances:
            for i in attendances:
                listids = [ids for ids in empid if ids.bioid == i.get('userid')]
                if listids:
                    for ids in listids:
                        emp_atten = attendanceobj.search([('employee_id', '=', ids.id)], limit=1)
                        if emp_atten:
                            if not emp_atten.check_out:
                                if i.get('attendances') > emp_atten.check_in:
                                    emp_atten.write({'check_out':i.get('attendances')})
                            if emp_atten.check_out:
                                if i.get('attendances') > emp_atten.check_out:
                                    dicts = {'employee_id': ids.id, 'check_in':i.get('attendances')}
                                    attenids = self.env['hr.attendance'].create(dicts)
                        else:
                            dicts = {'employee_id': ids.id, 'check_in':i.get('attendances')}
                            attenids = self.env['hr.attendance'].create(dicts)
                else:
                    attendance = {
                                    'guest_userid':i.get('userid'),
                                    'guest_datetime':i.get('attendances'),
                                    'guest_action': 'check In'
                                  }
                    self.env['guest.user'].create(attendance)
            self.env["last.attn"].create({"last_dt":str(attendances[-1].get('attendances'))})
        return True

    @api.multi
    def onclick_attendance(self):
        self._cron_biometric()
        return True

    @api.multi
    def onclick_unlock(self):
        for recs in self:
            zk = base.ZK(recs.bioip, int(recs.bioport), timeout=60, password=0, force_udp=False, ommit_ping=False)
            conn = zk.connect()
            conn.unlock(10)
            view = self.env.ref("zkteco_biometric.zkteco_action")
            return {
                    'name':'Door Status : Open',
                    'type': view.type,
                    'res_model': view.res_model,
                    'view_type': view.view_type,
                    'view_mode': view.view_mode,
                    'target': "new",
                    'context':{"message":"Door open for 10 Second."}
                    }
