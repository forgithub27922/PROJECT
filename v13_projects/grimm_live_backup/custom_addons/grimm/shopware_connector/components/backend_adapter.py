# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import socket
import logging
import xmlrpc.client
import urllib.parse

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth
from urllib3 import Retry

_logger = logging.getLogger(__name__)
import xmlrpc.client

SHOPWARE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class ShopwareLocation(object):

    def __init__(self, location, username, token):
        self.username = username
        self.token = token

        if not location.endswith('/'):
            location += '/'
        self._location = location + 'api/'

    @property
    def location(self):
        location = self._location
        #if not self.use_auth_basic:
        #    return location
        #assert self.auth_basic_username and self.auth_basic_password
        #replacement = "grimm:gastro@"
        #location = location.replace('://', '://' + replacement)
        return location

class ShopwareAPI(object):

    def __init__(self, location):
        """
        :param location: Shopware location
        :type location: :class:`ShopwareLocation`
        """
        self._location = location
        self._api = None
        self.base_url = location.location


    @property
    def api(self):
        if self._api is None:
            self.session = requests.Session()
            self.session.auth = HTTPDigestAuth(self._location.username, self._location.token)
            # Set up automatic retries on certain HTTP codes
            retry = Retry(
                total=5,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            api = self.session
            api.__enter__()
            self._api = api
        return self._api

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, type, value, traceback):
        if self._api is not None:
            self._api.__exit__(type, value, traceback)

    def call(self, method, api_call, payload=None):
        try:
            start = datetime.now()
            _logger.info("\n=====Called final api call is ===> %s %s%s%s",method,self._location.location,api_call,payload)
            response = self.api.request(method, self._location.location+api_call, json=payload, timeout=5)
            _logger.info("Response is ===> %s %s",response,response.status_code)
            try:
                _logger.info("\n\nReturn response from SHOPWARE is ===> %s",response.content.decode('utf-8'))
                if method == "post":
                    if response.status_code != 201:
                        raise FailedJobError("Odoo received error from shopware.\n\n%s" % (response.content.decode('utf-8')))
                result = response.json() #response.content.decode('utf-8')
                if result.get('success',False):
                    if method=='post':
                        result = result.get('data').get('id')
                    if method=='get':
                        result = result.get('data')
            except:
                _logger.error("api.call('%s') failed", api_call)
                raise
            else:
                _logger.debug("api.call('%s') returned %s in %s seconds",api_call,(datetime.now() - start).seconds)
            # Uncomment to record requests/responses in ``recorder``
            # record(method, arguments, result)
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s' % err)
        except xmlrpc.client.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise RetryableJobError(
                    'A protocol error caused the failure of the job:\n'
                    'URL: %s\n'
                    'HTTP/HTTPS headers: %s\n'
                    'Error code: %d\n'
                    'Error message: %s\n' %
                    (err.url, err.headers, err.errcode, err.errmsg))
            else:
                raise

class ShopwareCRUDAdapter(AbstractComponent):
    """ External Records Adapter for Shopware """

    _name = 'shopware.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.shopware.connector']
    _usage = 'backend.adapter'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _call(self, method, api_call, payload=None):
        try:
            shopware_api = getattr(self.work, 'shopware_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a shopware_api attribute with a '
                'ShopwareAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return shopware_api.call(method, api_call, payload)

class GenericShopwareAdapter(AbstractComponent):

    _name = 'shopware.adapter'
    _inherit = 'shopware.crud.adapter'

    _shopware_model = None
    _admin_path = None

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        ### It looks like https://partenics-dev.grimm-gastrobedarf.de/api/orders/?filter[0][property]=id&filter[0][value]=26
        return self._call('get','%s' % self._shopware_model,{})

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('%s' % self._shopware_model + '/' + str(id),
                          {'attributes': attributes})

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        return self._call('%s.list' % self._shopware_model, [filters])

    def create(self, data):
        """ Create a record on the external system """
        return self._call(self._target_odoo_model,'create',[data])

    def write(self, id, data):
        """ Update records on the external system """
        return self._call(self._shopware_model, 'write', [[int(id)], data])

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call(self._target_odoo_model, 'unlink', [id])