# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2014 Tom Kralidis
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
import os


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def str2None(v):
    return None if v == 'None' else v


DEBUG = False
SQLALCHEMY_ECHO = False

# Use Env vars via os.environ() from Dockerfile:
# makes it easier to override via Docker "environment"
# settings on running GHC Containers.
SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
# When True enables 'pre_ping' (optionally reconnect to DB) for the SQLALCHEMY create_engine options
SQLALCHEMY_ENGINE_OPTION_PRE_PING = os.environ['SQLALCHEMY_ENGINE_OPTION_PRE_PING']
# Replace None with 'your secret key string' in quotes
SECRET_KEY = os.environ['SECRET_KEY']

GHC_RETENTION_DAYS = int(os.environ['GHC_RETENTION_DAYS'])
GHC_PROBE_HTTP_TIMEOUT_SECS = int(os.environ['GHC_PROBE_HTTP_TIMEOUT_SECS'])
GHC_MINIMAL_RUN_FREQUENCY_MINS = int(os.environ['GHC_MINIMAL_RUN_FREQUENCY_MINS'])
GHC_SELF_REGISTER = str2bool(os.environ['GHC_SELF_REGISTER'])
GHC_NOTIFICATIONS = str2bool(os.environ['GHC_NOTIFICATIONS'])
GHC_NOTIFICATIONS_VERBOSITY = str2bool(os.environ['GHC_NOTIFICATIONS_VERBOSITY'])
GHC_WWW_LINK_EXCEPTION_CHECK = str2bool(os.environ['GHC_WWW_LINK_EXCEPTION_CHECK'])
GHC_LARGE_XML = str2bool(os.environ['GHC_LARGE_XML'])
GHC_NOTIFICATIONS_EMAIL = os.environ['GHC_NOTIFICATIONS_EMAIL']
GHC_ADMIN_EMAIL = os.environ['GHC_ADMIN_EMAIL']
GHC_SITE_TITLE = os.environ['GHC_SITE_TITLE']
GHC_SITE_URL = os.environ['GHC_SITE_URL']
GHC_RUNNER_IN_WEBAPP = str2bool(os.environ['GHC_RUNNER_IN_WEBAPP'])
GHC_REQUIRE_WEBAPP_AUTH = str2bool(os.environ['GHC_REQUIRE_WEBAPP_AUTH'])
GHC_BASIC_AUTH_DISABLED = str2bool(os.environ['GHC_BASIC_AUTH_DISABLED'])
GHC_VERIFY_SSL = str2bool(os.environ['GHC_VERIFY_SSL'])
GHC_LOG_LEVEL = int(os.environ['GHC_LOG_LEVEL'])
GHC_LOG_FORMAT = os.environ['GHC_LOG_FORMAT']

# Optional ENV set for GHC_PLUGINS (internal/core Plugins)
# if not set default from config_main.py applies
if os.environ.get('GHC_PLUGINS'):
    GHC_PLUGINS = os.environ['GHC_PLUGINS']

# Optional ENV set for GHC_USER_PLUGINS
# if not set none applies
if os.environ.get('GHC_USER_PLUGINS'):
    GHC_USER_PLUGINS = os.environ['GHC_USER_PLUGINS']

GHC_SMTP = {
    'server': os.environ['GHC_SMTP_SERVER'],
    'port': os.environ['GHC_SMTP_PORT'],
    'tls': str2bool(os.environ['GHC_SMTP_TLS']),
    'ssl': str2bool(os.environ['GHC_SMTP_SSL']),
    'username': str2None(os.environ.get('GHC_SMTP_USERNAME')),
    'password': str2None(os.environ.get('GHC_SMTP_PASSWORD'))
}

# TODO: provide for GHC Plugins

GHC_RELIABILITY_MATRIX = {
    'red': {
        'min': 0,
        'max': 49
    },
    'orange': {
        'min': 50,
        'max': 79
    },
    'green': {
        'min': 80,
        'max': 100
    }
}

GHC_MAP = {
    'url': 'https://tile.osm.org/{z}/{x}/{y}.png',
    'centre_lat': 42.3626,
    'centre_long': -71.0843,
    'maxzoom': 18,
    'subdomains': 1234,
}

GEOIP = {
    'plugin': 'GeoHealthCheck.plugins.geocode.webgeocoder.HttpGetGeocoder',
    'parameters': {
        'geocoder_url': os.environ['GHC_GEOIP_URL'],
        'lat_field': os.environ['GHC_GEOIP_LATFIELD'],
        'lon_field': os.environ['GHC_GEOIP_LONFIELD']
    }
}
