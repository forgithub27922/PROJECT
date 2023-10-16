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
import json
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth
from urllib3 import Retry

_logger = logging.getLogger(__name__)
import xmlrpc.client

SHOPWARE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class Shopware6Location(object):

    def __init__(self, location, client_id, client_secret, shopware6_backend):
        self.client_id = client_id
        self.client_secret = client_secret
        self.shopware6_backend_id = shopware6_backend

        if not location.endswith('/'):
            location += '/'
        self._location = location

    @property
    def location(self):
        location = self._location
        #if not self.use_auth_basic:
        #    return location
        #assert self.auth_basic_username and self.auth_basic_password
        #replacement = "grimm:gastro@"
        #location = location.replace('://', '://' + replacement)
        return location

class Shopware6API(object):

    def __init__(self, location):
        """
        :param location: Shopware6 location
        :type location: :class:`Shopware6 Location`
        """
        self._location = location
        self._api = None
        self.base_url = location.location


    @property
    def api(self):
        if self._api is None:
            self.session = requests.Session()
            self.session.auth = HTTPDigestAuth(self._location.client_id, self._location.client_secret)
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


    def _get_fresh_token(self, api_call='api/oauth/token', shopware6_backend = False):
        def call_token_api():
            response = self.api.request('POST', self._location.location + api_call,
                                        auth=(self._location.client_id, self._location.client_secret),
                                        data={'grant_type': 'client_credentials'})
            return response.json()

        if shopware6_backend.token_info_id:
            if shopware6_backend.token_info_id.is_token_expired():
                token_data = call_token_api()
                shopware6_backend.token_info_id.access_token = token_data.get("access_token")
        else:
            shopware6_backend.set_token_info(call_token_api())
        return shopware6_backend.token_info_id.access_token

    def call(self, method, api_call, payload={}):
        try:
            start = datetime.now()
            method = method.upper()
            timeout = 6 if '_action/sync' not in api_call else 50
            shopware6_backend = self._location.shopware6_backend_id
            if not shopware6_backend.connector_status:
                raise RetryableJobError("Connector is disable so job will be retried later.", ignore_retry=True)
            # if shopware6_backend.version == "6.4.1.0": # Version parameter removed since 6.4.1.0 version
            api_call = api_call.replace("/v3","")
            api_call = api_call.replace("/v2", "")
            fresh_token = self._get_fresh_token(shopware6_backend=self._location.shopware6_backend_id)
            assert fresh_token
            headers = {'Authorization': fresh_token, 'Accept': '*/*'}
            if method == "DELETE": # Before deleting just checking record exists ? if exists continue for delete operation else return True (Because record does not exists.)
                is_exists = self.api.request("GET", self._location.location + api_call, headers=headers, json=payload,timeout=timeout)
                if is_exists.status_code == 404:
                    return is_exists.status_code
            if  method in ["POST"] and ('_action/media' not in api_call and '_action/document' not in api_call and 'ratepay/order-management/deliver' not in api_call and '_action/sync' not in api_call and 'swpa-sort' not in api_call):
                api_call += "?_response=true"
            if '_action/media' in api_call or '_action/document' in api_call :
                headers["Content-Type"] = "image/jpeg" if '_action/media' in api_call else 'application/pdf'

                if shopware6_backend.is_print_log:
                    _logger.info("\n=====Called final ap...i call is ===> %s %s%s%s"% (method, self._location.location, api_call, len(payload)))
                if type(payload) == type({}):
                    headers["Content-Type"] = "application/json"
                    response = self.api.request(method, self._location.location + api_call, headers=headers,json=payload, timeout=timeout)
                else:
                    response = self.api.request(method, self._location.location+api_call,headers=headers, data=payload, timeout=timeout)
            else:
                if shopware6_backend.is_print_log:
                    _logger.info("\n=====Called final api call is ===> %s %s%s%s"%(method, self._location.location,api_call, payload))
                response = self.api.request(method, self._location.location + api_call, headers=headers, json=payload, timeout=timeout)

            if shopware6_backend.is_print_log:
                _logger.info("Response code is ===> %s"%response)
            response_code = response.status_code
            try:
                if shopware6_backend.is_print_log:
                    _logger.info("\n\nReturn response from SHOPWARE6 is ===> %s"% response.content.decode('utf-8'))
                if response_code >= 200 and response_code <= 299:
                    if response_code == 200 and method in ['POST']:
                        result = response.json()  # We have to return only ID after creating record on shopware6
                        if result.get("success",False):
                            result = result.get("success")
                        else:
                            result = result.get('data',{}).get('id',{}) if result.get('data',{}).get('id',False) else result
                    elif method in ["GET"]:
                        result = response.json()
                        #result = result.get('data', result)
                    else:
                        result = {}

                else:
                    raise FailedJobError("Odoo received error from shopware6.\n\n%s" % (response.content.decode('utf-8')))
            except:
                _logger.error("api.call('%s %s') failed"% (method, api_call))
                raise
            else:
                _logger.debug("api.call('%s') returned in %s seconds"%(api_call,(datetime.now() - start).seconds))
            return result.get("documentId",result) if type(result) == type({}) else result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s ==== %s %s' % (err, method, api_call))
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

class Shopware6CRUDAdapter(AbstractComponent):
    """ External Records Adapter for Shopware6 """

    _name = 'shopware6.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.shopware6.connector']
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
            shopware6_api = getattr(self.work, 'shopware6_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a shopware6_api attribute with a '
                'ShopwareAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return shopware6_api.call(method, api_call, payload)

class GenericShopware6Adapter(AbstractComponent):

    _name = 'shopware6.adapter'
    _inherit = 'shopware6.crud.adapter'

    _shopware_model = None
    _admin_path = None

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('GET', '%s' % self._shopware_uri, [filters] if filters else [{}])

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('GET', '%s%s' % (self._shopware_uri, id), [{}])

    def create(self, data):
        """ Create Partner records on the external system """
        return self._call('POST', '%s' % self._shopware_uri, data)

    def write(self, id, data):
        """ Update records on the external system """
        # XXX actually only ol_catalog_product.update works
        # the PHP connector maybe breaks the catalog_product.update
        return self._call('PATCH', self._shopware_uri + id, data)

    def delete(self, id):
        """ Delete partner records on the external system """
        return self._call('DELETE', self._shopware_uri + id, {})