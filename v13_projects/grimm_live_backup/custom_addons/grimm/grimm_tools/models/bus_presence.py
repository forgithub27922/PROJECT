# -*- coding: utf-8 -*-
import datetime
import time

from odoo import api, fields, models
from odoo import tools
from odoo.addons.bus.models.bus import TIMEOUT
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

DISCONNECTION_TIMER = TIMEOUT + 5
AWAY_TIMER = 1800  # 30 minutes


class BusPresence(models.Model):
    """ Grimm inherited this model and method due to concurrent update.
    SERIALIZATION_FAILURE, retry 1/5 in 0.5216 sec...
    ERROR produktion odoo.sql_db: bad query: UPDATE "bus_presence" SET "last_presence"='2021-03-02 10:41:20.736758' WHERE id IN (64)
    ERROR: could not serialize access due to concurrent update
    """

    _inherit = 'bus.presence'

    @api.model
    def update(self, inactivity_period):
        """ Updates the last_poll and last_presence of the current user
            :param inactivity_period: duration in milliseconds
        """
        presence = self.search([('user_id', '=', self._uid)], limit=1)
        # compute last_presence timestamp
        last_presence = datetime.datetime.now() - datetime.timedelta(milliseconds=inactivity_period)
        values = {
            'last_poll': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        }
        # update the presence or a create a new one
        if not presence:  # create a new presence for the user
            values['user_id'] = self._uid
            values['last_presence'] = last_presence
            self.create(values)
        # else:  # update the last_presence if necessary, and write values
        #     if presence.last_presence < last_presence:
        #         values['last_presence'] = last_presence
        #     # Hide transaction serialization errors, which can be ignored, the presence update is not essential
        #     if self.env['ir.config_parameter'].sudo().get_param('last_presence',False):
        #         with tools.mute_logger('odoo.sql_db'):
        #             presence.write(values)
        # # avoid TransactionRollbackError
        #self.env.cr.commit() # TODO : check if still necessary
