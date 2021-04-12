# =================================================================
#
# Authors: Rob van Loon <borrob@me.com>
#
# Copyright (c) 2021 Rob van Loon
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import requests
import json

from GeoHealthCheck.init import App
from GeoHealthCheck.geocoder import Geocoder


class HttpGeocoder(Geocoder):
    """
    A base class for geocoders on the web.

    It is intended to use a *subclass* of this class and implement the
    `make_call` method.
    """

    NAME = 'Http geocoder plugin'

    DESCRIPTION = 'Geolocator service via a http request. Use a subclass of ' \
                  'this plugin and implement the make_call function.'

    PARAM_DEFS = {}
    REQUEST_TEMPLATE = ''
    REQUEST_HEADERS = {}

    def __init__(self):
        super().__init__()

    def init(self, geocoder_vars):
        super().init(geocoder_vars)
        self._geocoder_url = geocoder_vars.get('geocoder_url')
        self._lat_field = geocoder_vars.get('lat_field')
        self._lon_field = geocoder_vars.get('lon_field')
        self._parameters = geocoder_vars.get('parameters', self.PARAM_DEFS)
        self._template = geocoder_vars.get('template', self.REQUEST_TEMPLATE)

    def get_request_headers(self):
        headers = Geocoder.copy(self.REQUEST_HEADERS)
        return headers

    # Lifecycle
    def before_request(self):
        """ Before running actual request to service"""
        pass

    # Lifecycle
    def after_request(self):
        """ After running actual request to service"""
        pass

    def get_request_string(self):
        request_string = None
        if self._template:
            request_string = self._template
            if '?' in self._geocoder_url and self._template[0] == '?':
                self._template = '&' + self._template[1:]

            if self._parameters:
                params_names = self._parameters.keys()
                params = {}
                for param in params_names:
                    params.update({param: self._parameters.get(param).
                                   get('value')})
                    if self._parameters.get(param).get('type') == 'stringlist':
                        params.update({param: ','.join(params.get(param))})
                request_string = self._template.format(** params)
        return request_string

    # Lifecycle
    def run_request(self, ip):
        """ Prepare actual request to service"""

        self._response = None
        # Actualize request query string or POST body
        # by substitution in template.
        request_string = self.get_request_string()

        base_url = self._geocoder_url.format(hostname=ip) if ip \
            else self._geocoder_url
        self.log('Requesting: url=%s' % (base_url))

        try:
            self.make_call(base_url, request_string)
        except requests.exceptions.RequestException as e:
            self.log("Request Err: %s %s" % (e.__class__.__name__, str(e)))

        if self._response:
            self.log('response: status=%d' % self._response.status_code)

            if self._response.status_code // 100 in [4, 5]:
                self.log('Error response: %s' % (str(self._response.text)))

    # Lifecycle
    def make_call(self, base_url, request_string):
        pass

    # Lifecycle
    def perform_request(self, ip):
        try:
            self.before_request()

            try:
                self.run_request(ip)
            except Exception as e:
                msg = "Perform_request Err: %s %s" % \
                      (e.__class__.__name__, str(e))

            self.after_request()

        except Exception as e:
            # We must never bailout because of Exception
            msg = "GeoLocator Err: %s %s" % (e.__class__.__name__, str(e))
            self.log(msg)

    # Lifecycle
    def parse_result(self):
        self._lat = 0
        self._lon = 0
        try:
            content = json.loads(self._response.text)
            self._lat = content[self._lat_field]
            self._lon = content[self._lon_field]
        except Exception as err:  # skip storage
            msg = 'Could not derive coordinates: %s' % err
            self.log(msg)

        self._result = (self._lat, self._lon)

    def locate(self, ip):
        """
        Class method to create and run a single Probe
        instance. Follows strict sequence of method calls.
        Each method can be overridden in subclass.
        """
        self._response = ''
        self._result = (0, 0)

        # Perform request
        self.perform_request(ip)

        # Determine result
        self.parse_result()

        # Return result
        return self._result


class HttpGetGeocoder(HttpGeocoder):
    """
    A geocoder plugin using a http GET request.

    Use the `init` method (**not** the dunder methode) to initialise the
    geocoder. Provide a dict with keys: `geocoder_url`, `lat_field`,
    `lon_field`, and optional `template` and `parameters`. The `geocoder_url`
    parameter should include `{hostname}` where the `locate` function will
    substitute the server name that needs to be located. The `lat_field` and
    `lon_field` parameters specify the field names of the lat/lon in the json
    response.
    """

    NAME = 'Http geocoder plugin based on a GET request.'

    DESCRIPTION = 'Geolocator service via a http GET request.'

    def __init__(self):
        super().__init__()

    def make_call(self, base_url, request_string=''):
        url = base_url + request_string if request_string else base_url
        self._response = requests.get(
            url,
            timeout=App.get_config()['GHC_PROBE_HTTP_TIMEOUT_SECS'],
            headers=self.get_request_headers())


class HttpPostGeocoder(HttpGeocoder):
    """
    A geocoder plugin using a http POST request.

    Use the `init` method (**not** the dunder methode) to initialise the
    geocoder. Provide a dict with keys: `geocoder_url`, `lat_field`,
    `lon_field`, and optional `template` and `parameters`. The `geocoder_url`
    parameter should include `{hostname}` where the `locate` function will
    substitute the server name that needs to be located. The `lat_field` and
    `lon_field` parameters specify the field names of the lat/lon in the json
    response.
    """

    NAME = 'Http geocoder plugin based on a POST request.'

    DESCRIPTION = 'Geolocator service via a http POST request.'

    def __init__(self):
        super().__init__()

    def make_call(self, base_url, request_string=''):
        self._response = requests.post(
            base_url,
            timeout=App.get_config()['GHC_PROBE_HTTP_TIMEOUT_SECS'],
            data=request_string,
            headers=self.get_request_headers())
