#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2020 Dipak Suthar
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError
from datetime import datetime, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)

class Base(models.AbstractModel):
    """
    We have inherited this method because odoo base allowed only class field but in connector
    we also used some extra fields like magento_id or shopware_id etc.
    So its removing unwanted fields.
    """
    _inherit = "base"
    def _update_cache(self, values, validate=True):
        """ Update the cache of ``self`` with ``values``.

            :param values: dict of field values, in any format.
            :param validate: whether values must be checked
        """
        def is_monetary(pair):
            return pair[0].type == 'monetary'

        self.ensure_one()
        cache = self.env.cache
        fields = self._fields
        # Grimm START
        dup_values = values.copy()
        val_keys = list(values.keys())
        for key in val_keys:
            if key not in list(self._fields):
                del values[key]
        # Grimm END
        try:
            field_values = [(fields[name], value) for name, value in values.items()]
        except KeyError as e:
            raise ValueError("Invalid field %r on model %r" % (e.args[0], self._name))
        #Grimm START
        values.update(dup_values)
        # Grimm END

        # convert monetary fields last in order to ensure proper rounding
        for field, value in sorted(field_values, key=is_monetary):
            cache.set(self, field, field.convert_to_cache(value, self, validate))

            # set inverse fields on new records in the comodel
            if field.relational:
                inv_recs = self[field.name].filtered(lambda r: not r.id)
                if not inv_recs:
                    continue
                for invf in self._field_inverses[field]:
                    # DLE P98: `test_40_new_fields`
                    # /home/dle/src/odoo/master-nochange-fp/odoo/addons/test_new_api/tests/test_new_fields.py
                    # Be careful to not break `test_onchange_taxes_1`, `test_onchange_taxes_2`, `test_onchange_taxes_3`
                    # If you attempt to find a better solution
                    for inv_rec in inv_recs:
                        if not cache.contains(inv_rec, invf):
                            val = invf.convert_to_cache(self, inv_rec, validate=False)
                            cache.set(inv_rec, invf, val)
                        else:
                            invf._update(inv_rec, self)

    def write(self, vals):
        result = super(Base, self).write(vals)
        for record in self:
            for key,value in vals.items():
                all_fields = self.fields_get()
                if all_fields.get(key, False) and all_fields.get(key).get("translate"):
                    Translation = self.env["ir.translation"].search([
                        ('lang', '=', self.env.user.lang or 'de_DE'),
                        ('name', '=', "%s,%s" % (record._name, key)),
                        ('res_id', '=', record.id),
                    ])
                    if Translation:
                        Translation.value = vals.get(key)
        return result

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            val_keys = list(vals.keys())
            for key in val_keys:
                if key not in list(self._fields):
                    del vals[key]
        result = super(Base, self).create(vals_list)
        return result

def _select_nextval(cr, seq_name):
    cr.execute("SELECT nextval('%s')" % seq_name)
    return cr.fetchone()

def _update_nogap(self, number_increment):
    number_next = self.number_next
    self._cr.execute("SELECT number_next FROM %s WHERE id=%s FOR UPDATE NOWAIT" % (self._table, self.id))
    self._cr.execute("UPDATE %s SET number_next=number_next+%s WHERE id=%s " % (self._table, number_increment, self.id))
    self.invalidate_cache(['number_next'], [self.id])
    return number_next

class IrSequence(models.Model):
    """ Sequence model.

    The sequence model allows to define and use so-called sequence objects.
    Such objects are used to generate unique identifiers in a transaction-safe
    way.

    """
    _inherit = 'ir.sequence'

    def get_next_char(self, number_next, seq_prefix=False, seq_suffix=False):

        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
        if seq_prefix:
            interpolated_prefix = seq_prefix
        if seq_suffix:
            interpolated_suffix = seq_suffix
        return interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix

    def _next(self, sequence_date=None):
        """ Returns the next number in the preferred sequence in all the ones given in self."""
        if not self.use_date_range:
            return self._next_do()
        # date mode
        dt = fields.Date.today()
        if self._context.get('ir_sequence_date'):
            dt = self._context.get('ir_sequence_date')
        seq_date = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
        if not seq_date:
            seq_date = self._create_date_range_seq(dt)
        return seq_date.with_context(ir_sequence_date_range=seq_date.date_from, ir_sequence_date = dt)._next()

class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    seq_prefix = fields.Char(string='Prefix')
    seq_suffix = fields.Char(string='Suffix')

    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or str(self._context.get('ir_sequence_date')).split("+")[0])
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or str(self._context.get('ir_sequence_date_range')))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            return res

        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.seq_prefix, d)
            interpolated_suffix = _interpolate(self.seq_suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
        return interpolated_prefix, interpolated_suffix

    def _next(self):
        if self.sequence_id.implementation == 'standard':
            number_next = _select_nextval(self._cr, 'ir_sequence_%03d_%03d' % (self.sequence_id.id, self.id))
        else:
            number_next = _update_nogap(self, self.sequence_id.number_increment)
        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
        if not interpolated_prefix:
            interpolated_prefix = False
        if not interpolated_suffix:
            interpolated_suffix = False
        return self.sequence_id.get_next_char(number_next, seq_prefix=interpolated_prefix, seq_suffix=interpolated_suffix)